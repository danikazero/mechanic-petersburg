extends Control

# Vertical slice prototype: narrative, diagnostic decisions and persistent branch flags.
# Equipment logic is fictional and must be validated against the exact SCC 61 revision.
const PHONE = preload("res://scripts/phone.gd")
const APARTMENT = preload("res://scenes/Apartment.tscn")
const ROOMS := {
	"apartment": APARTMENT, "departure": APARTMENT,
	"street": preload("res://scenes/Street.tscn"),
	"kitchen": preload("res://scenes/Kitchen.tscn"),
	"district": preload("res://scenes/District.tscn")
}
const TEST_LOCATIONS := {
	"apartment": "Квартира", "street": "Квартал Бенуа",
	"kitchen": "Кухня ресторана", "district": "Спальный район"
}
const SAVE := "user://prologue_v02.cfg"
const ROOM_STAGES := {"apartment": "street", "departure": "street", "street": "kitchen", "kitchen": "inspection", "district": "district_panel"}
const STAGES := ["apartment", "call", "departure", "street", "phone_status", "kitchen", "inspection", "diagnosis", "heater", "sensor", "board", "replacement", "failure", "decline", "moving", "district", "district_panel", "first_job"]
const FG := Color("f1eee6")
const MUTED := Color("aeb7c1")
const ACCENT := Color("e6ad58")
const BAD := Color("e17c70")

var test_mode := false
var stage := "apartment"
var took_job := false
var phone_origin := "apartment"
var phone_position := Vector2.ZERO
var heater_tested := false
var heater_replaced := false
var experience := 0
var game_seconds := 0.0
var displayed_minute := -1
var clock_label: Label
var money := 3800
var zhenya_trust := 50
var electronics_skill := 1
var body: VBoxContainer

func _ready() -> void:
	test_mode = "--locations" in OS.get_cmdline_user_args()
	if OS.has_feature("web"):
		var location := JavaScriptBridge.get_interface("location")
		if location != null:
			test_mode = test_mode or "test=1" in String(location.search).trim_prefix("?").split("&")
	if test_mode:
		go_to_test_location("street")
		return
	load_progress()
	var reopen_phone := stage in ["call", "phone_status"]
	if reopen_phone:
		stage = phone_origin if phone_origin in ["apartment", "departure", "street"] else "apartment"
	show_stage()
	if reopen_phone:
		open_phone(get_child(0))

func _process(delta: float) -> void:
	game_seconds += delta * 5.0
	var minute := int(game_seconds / 60.0)
	if minute != displayed_minute and is_instance_valid(clock_label):
		displayed_minute = minute
		var time := (8 * 60 + minute) % 1440
		clock_label.text = "%02d:%02d" % [floori(time / 60.0), time % 60]

func save_progress() -> void:
	if test_mode:
		return
	var data := ConfigFile.new()
	for key in ["stage", "took_job", "heater_tested", "heater_replaced", "money", "zhenya_trust", "experience", "game_seconds", "phone_origin", "phone_position"]:
		data.set_value("prologue", key, get(key))
	var result := data.save(SAVE)
	if result != OK:
		push_warning("Could not save prologue: %s" % error_string(result))

func load_progress() -> void:
	var data := ConfigFile.new()
	if data.load(SAVE) != OK:
		return
	for key in ["stage", "took_job", "heater_tested", "heater_replaced", "money", "zhenya_trust", "experience", "game_seconds", "phone_origin", "phone_position"]:
		var value = data.get_value("prologue", key, get(key))
		if typeof(value) == typeof(get(key)) and (key != "stage" or value in STAGES):
			set(key, value)

func show_room() -> void:
	var room = ROOMS[stage].instantiate()
	room.room_id = stage
	room.has_job = took_job
	room.interacted.connect(func():
		next_stage("apartment" if stage == "street" and not took_job else ROOM_STAGES[stage])
	)
	room.phone_opened.connect(func(): open_phone(room))
	add_child(room)
	if phone_position != Vector2.ZERO and (stage == phone_origin or (stage == "departure" and phone_origin == "apartment")):
		room.player.position = phone_position
		phone_position = Vector2.ZERO
	var overlay := CanvasLayer.new()
	add_child(overlay)
	clock_label = label_text("", 21, ACCENT)
	clock_label.position = Vector2(1020, 22)
	clock_label.size = Vector2(100, 30)
	clock_label.autowrap_mode = TextServer.AUTOWRAP_OFF
	clock_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	overlay.add_child(clock_label)


func open_phone(room: Node2D) -> void:
	if room.phone_visible:
		return
	room.phone_visible = true
	room.reset_stick()
	var layer := CanvasLayer.new()
	layer.layer = 5
	add_child(layer)
	var panel := PHONE.new()
	layer.add_child(panel)
	var minute := (480 + int(game_seconds / 60.0)) % 1440
	panel.setup(took_job, "%02d:%02d" % [floori(minute / 60.0), minute % 60])
	panel.dismissed.connect(func():
		remove_child(layer)
		layer.queue_free()
		room.phone_visible = false
	)
	panel.accepted.connect(func():
		took_job = true
		phone_origin = stage
		phone_position = room.player.position
		next_stage("street" if stage == "street" else "departure")
	)
	panel.declined.connect(func():
		took_job = false
		zhenya_trust += 10
		next_stage("decline")
	)


func label_text(value: String, size: int = 21, tint: Color = FG) -> Label:
	var l := Label.new()
	l.text = value
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", tint)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l

func button_text(value: String, fn: Callable, enabled: bool = true) -> void:
	var b := Button.new()
	b.text = value
	b.custom_minimum_size = Vector2(0, 51)
	b.disabled = not enabled
	b.pressed.connect(fn)
	body.add_child(b)

func note(value: String, tint: Color = MUTED) -> void:
	body.add_child(label_text(value, 19, tint))

func next_stage(value: String) -> void:
	stage = value
	save_progress()
	show_stage()

func go_to_test_location(destination: String) -> void:
	if not test_mode or not TEST_LOCATIONS.has(destination):
		return
	took_job = destination in ["street", "kitchen"]
	phone_origin = "apartment"
	phone_position = Vector2.ZERO
	heater_tested = false
	heater_replaced = false
	next_stage(destination)

func add_location_picker() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 4
	add_child(layer)

	var open := Button.new()
	open.text = "Локации"
	open.position = Vector2(912, 61)
	open.size = Vector2(216, 60)
	open.focus_mode = Control.FOCUS_NONE
	open.add_theme_font_size_override("font_size", 24)
	layer.add_child(open)
	open.pressed.connect(func(): open_location_menu(layer, open))

func open_location_menu(layer: CanvasLayer, open: Button) -> void:
	open.hide()
	var room = get_child(0)
	var room_is_active := ROOM_STAGES.has(stage)
	if room_is_active:
		room.reset_stick()
		room.process_mode = Node.PROCESS_MODE_DISABLED

	var shade := ColorRect.new()
	shade.color = Color("#141318bd")
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(shade)

	var panel := PanelContainer.new()
	panel.position = Vector2(366, 106)
	panel.size = Vector2(420, 432)
	shade.add_child(panel)
	var margin := MarginContainer.new()
	for side in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 21)
	panel.add_child(margin)
	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", 8)
	margin.add_child(list)
	list.add_child(label_text("Локации", 30, ACCENT))
	list.add_child(label_text("Тестовый режим", 19, MUTED))

	for destination: String in TEST_LOCATIONS:
		var choice := Button.new()
		choice.text = TEST_LOCATIONS[destination]
		choice.custom_minimum_size.y = 51
		choice.add_theme_font_size_override("font_size", 22)
		choice.pressed.connect(go_to_test_location.bind(destination))
		list.add_child(choice)
	var back := Button.new()
	back.text = "Закрыть"
	back.custom_minimum_size.y = 48
	back.add_theme_font_size_override("font_size", 21)
	list.add_child(back)
	back.pressed.connect(func():
		layer.remove_child(shade)
		shade.queue_free()
		if room_is_active:
			room.process_mode = Node.PROCESS_MODE_INHERIT
		open.show()
	)

func show_stage() -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	displayed_minute = -1
	if ROOM_STAGES.has(stage):
		show_room()
		if test_mode:
			add_location_picker()
		return
	var outer := MarginContainer.new()
	outer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	outer.add_theme_constant_override("margin_left", 36)
	outer.add_theme_constant_override("margin_top", 22)
	outer.add_theme_constant_override("margin_right", 36)
	outer.add_theme_constant_override("margin_bottom", 22)
	add_child(outer)
	var scroll := ScrollContainer.new()
	outer.add_child(scroll)
	body = VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 13)
	scroll.add_child(body)
	var heading := HBoxContainer.new()
	body.add_child(heading)
	var title := label_text("МЕХАНИК ПЕТЕРБУРГА  /  ПРОТОТИП 0.2", 16, ACCENT)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading.add_child(title)
	clock_label = label_text("", 21, ACCENT)
	heading.add_child(clock_label)
	match stage:
		"inspection": inspection()
		"diagnosis": diagnosis()
		"heater": heater()
		"sensor": locked_part("ДАТЧИК ТЕМПЕРАТУРЫ", "Диагностика датчика пока недоступна: не хватает навыка.")
		"board": locked_part("ПЛАТА УПРАВЛЕНИЯ", "Электроника: 1. Требуется: 15. Диагностика платы недоступна.")
		"replacement": replacement()
		"failure": failure()
		"decline": decline()
		"moving": moving()
		"district_panel": district()
		"first_job": first_job()
	if test_mode:
		add_location_picker()

func inspection() -> void:
	body.add_child(label_text("RATIONAL SCC 61 — ВНЕШНИЙ ОСМОТР", 30))
	note("Женя сообщает, что камера перестала нагреваться. По внешнему осмотру причина неясна.")
	button_text("Перейти к внутренним узлам", func(): next_stage("diagnosis"))
	button_text("Закрыть панель", func(): next_stage("kitchen"))

func diagnosis() -> void:
	body.add_child(label_text("RATIONAL SCC 61 — ДИАГНОСТИКА", 30))
	note("Жалоба: отсутствует нормальный нагрев. Выбери узел для проверки.")
	note("Навык электрики: 3  /  Электроника: %d" % electronics_skill, ACCENT)
	button_text("Нагревательный элемент (ТЭН)", func(): next_stage("heater"))
	button_text("Датчик температуры — недоступно", func(): next_stage("sensor"))
	button_text("Плата управления — недоступно", func(): next_stage("board"))
	button_text("Вернуться к внешнему осмотру", func(): next_stage("inspection"))
	button_text("Отказаться от ремонта и предупредить Женю", func(): zhenya_trust += 10; next_stage("decline"))

func heater() -> void:
	body.add_child(label_text("СИСТЕМА НАГРЕВА — ТЭН", 30))
	if not heater_tested:
		note("После безопасного отключения и подготовки к измерению можно проверить нагревательный элемент.")
		button_text("Проверить сопротивление ТЭНа", record_heater_test)
	else:
		note("Результат: обрыв цепи. ТЭН неисправен.", BAD)
		note("ВНИМАНИЕ: причина повреждения ТЭНа не установлена.", ACCENT)
		button_text("Заменить ТЭН", func(): next_stage("replacement"))
	button_text("Вернуться к списку узлов", func(): next_stage("diagnosis"))

func record_heater_test() -> void:
	heater_tested = true
	save_progress()
	show_stage()

func locked_part(part_name: String, explanation: String) -> void:
	body.add_child(label_text(part_name, 30))
	note("ДОСТУП ЗАКРЫТ", BAD)
	note(explanation)
	note("Можно отказаться от работы, не пытаясь устранить неисправность наугад.")
	button_text("Вернуться", func(): next_stage("diagnosis"))

func replacement() -> void:
	body.add_child(label_text("РЕМОНТ — РЕШЕНИЕ", 30))
	note("ТЭН действительно неисправен. Но первопричина пока неизвестна.")
	button_text("Установить новый ТЭН и сдать аппарат", complete_repair)
	button_text("Остановить ремонт и сообщить об ограничениях диагностики", func(): zhenya_trust += 10; next_stage("decline"))

func complete_repair() -> void:
	heater_replaced = true
	money -= 2400
	experience += 5
	zhenya_trust = 0
	next_stage("failure")

func failure() -> void:
	body.add_child(label_text("ПОВТОРНАЯ ПОЛОМКА", 31, BAD))
	note("После замены и запуска аппарат вновь перегревается. Новый ТЭН выходит из строя.")
	note("Позже специалист обнаруживает повреждения датчика и платы управления после скачка напряжения.")
	note("Женя: «Ты же сказал, что починил. Теперь всё стало ещё хуже!»")
	note("Расходы и претензии увеличивают долги. Времени и денег на аренду больше нет.")
	note("Запчасть: −2 400 ₽. Опыт: +5.", ACCENT)
	button_text("Собрать вещи", func(): next_stage("moving"))

func decline() -> void:
	body.add_child(label_text("ПРОФЕССИОНАЛЬНЫЙ ОТКАЗ", 30))
	note("Ты не берёшься за работу, которую не можешь полноценно проверить. Женя недоволен срочностью, но оборудование не повреждено твоим ремонтом.")
	note("Однако долг за квартиру никуда не исчез. Хозяин требует освободить жильё.")
	button_text("Собрать вещи", func(): next_stage("moving"))

func moving() -> void:
	body.add_child(label_text("ВЫСЕЛЕНИЕ", 31))
	note("Вечер. Дождь. Чемодан с инструментами, сумка с одеждой, ключи на ладони.")
	if heater_replaced:
		note("Ты потерял заказ, деньги и доверие Жени. В телефоне осталась заявка №001.", BAD)
	else:
		note("Ты сохранил остаток денег и не повредил чужую технику, но квартиру всё равно пришлось оставить.")
	button_text("Уехать в спальный район", func(): next_stage("district"))

func district() -> void:
	body.add_child(label_text("ГЛАВА 1 — НАЧАТЬ С НУЛЯ", 31))
	note("Спальный район. Сырая комната, старый диван, панельные дома за окном.")
	note("Телефон вибрирует. Неизвестный номер: «Мастер? У нас в шаверме гриль не греет. Посмотреть сможешь? Только недорого».")
	note("Деньги: %d ₽    Опыт: %d    Доверие Жени: %d" % [money, experience, zhenya_trust], ACCENT)
	note("Состояние заявки №001: %s" % ("неудачный ремонт" if heater_replaced else "отказ от заказа"), ACCENT)
	button_text("Принять первую заявку из шавермичной", func(): next_stage("first_job"))
	button_text("Начать пролог заново", func(): reset_game())

func first_job() -> void:
	body.add_child(label_text("ЗАЯВКА №002 — ШАВЕРМИЧНАЯ", 30))
	note("Контактный гриль не держит температуру. Клиент предлагает 1 200 ₽ за работу и пытается торговаться.")
	note("Это конец первого вертикального среза. Следующий этап — свободное перемещение, интерьер и полноценная диагностика гриля.", ACCENT)
	button_text("Вернуться в комнату", func(): next_stage("district"))

func reset_game() -> void:
	stage = "apartment"
	phone_origin = "apartment"
	phone_position = Vector2.ZERO
	took_job = false
	heater_tested = false
	heater_replaced = false
	money = 3800
	zhenya_trust = 50
	experience = 0
	game_seconds = 0.0
	save_progress()
	show_stage()
