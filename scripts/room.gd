extends Node2D

signal interacted
signal phone_opened

const ROOM_SIZE := Vector2(1500, 850)
const SPEED := 112.5
const PLAYER_RADIUS := 17.0
const REACH := 78.0
const FRAME_SIZE := Vector2(28, 56)
const ATLAS_ROWS := [0, 1, 2, 1, 0, 4, 3, 4]
const WALK_COLUMNS := [1, 2, 3, 4]
const WALLS := [
	Rect2(0, 0, 1500, 32), Rect2(0, 818, 1500, 32),
	Rect2(0, 0, 32, 850), Rect2(1468, 0, 32, 850)
]

var player := Node2D.new()
var obstacles: Array[Rect2] = []
var target := Rect2()
var has_job := false
var sprite := AnimatedSprite2D.new()
var phone: Button
var phone_visible := false

func is_apartment() -> bool:
	return room_id in ["apartment", "departure"]

func has_phone_menu() -> bool:
	return is_apartment() or room_id == "street"
var furniture: Array[Rect2] = []
@export var room_id := "apartment"
var stick_id := -1
var mouse_stick := false
var stick_vector := Vector2.ZERO
var prompt := Label.new()
var action := Button.new()
var stick := Control.new()
var facing := 2
var web_stick: JavaScriptObject
var diagnostics: Label
var touch_starts := 0
var touch_drags := 0
var travel := 0.0

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	configure()
	add_child(player)
	setup_sprite()
	var camera := Camera2D.new()
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = int(ROOM_SIZE.x)
	camera.limit_bottom = int(ROOM_SIZE.y)
	player.add_child(camera)
	obstacles.assign(WALLS)
	obstacles.append_array(furniture)
	if is_apartment():
		obstacles.append(Rect2(0, 0, 1500, 233))
	player.position = Vector2(560, 500) if is_apartment() else Vector2(470, 480)

	var hud := CanvasLayer.new()
	add_child(hud)
	if OS.get_name() == "Web" and JavaScriptBridge.eval("new URLSearchParams(location.search).get('diagnostics') === '1'") == true:
		diagnostics = Label.new()
		diagnostics.position = Vector2(24, 70)
		diagnostics.add_theme_font_size_override("font_size", 26)
		diagnostics.add_theme_color_override("font_shadow_color", Color.BLACK)
		diagnostics.add_theme_constant_override("shadow_offset_x", 2)
		diagnostics.add_theme_constant_override("shadow_offset_y", 2)
		diagnostics.mouse_filter = Control.MOUSE_FILTER_IGNORE
		hud.add_child(diagnostics)
	stick.position = Vector2(24, 462)
	stick.size = Vector2(164, 164)
	stick.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(stick)
	stick.draw.connect(draw_stick)
	action.position = Vector2(878, 548)
	action.size = Vector2(250, 76)
	action.focus_mode = Control.FOCUS_NONE
	style_hud_button(action, "hud-action", "hud-disabled")
	action.pressed.connect(interact)
	hud.add_child(action)
	prompt.position = Vector2(24, 22)
	prompt.add_theme_font_size_override("font_size", 24)
	hud.add_child(prompt)
	if has_phone_menu():
		phone = Button.new()
		phone.text = "Телефон"
		phone.tooltip_text = "Открыть телефон (Tab)"
		phone.position = Vector2(878, 457)
		phone.size = Vector2(250, 76)
		phone.focus_mode = Control.FOCUS_NONE
		style_hud_button(phone, "hud-phone", "hud-phone")
		phone.pressed.connect(func(): phone_opened.emit())
		hud.add_child(phone)
	if OS.get_name() == "Web":
		setup_web_stick()
	update_hud()

func setup_web_stick() -> void:
	# Read browser pointer state each frame, including when a touch stays still.
	JavaScriptBridge.eval("""
		if (!window.mechanicStick) {
			const state = window.mechanicStick = { id: -1, x: 0, y: 0, starts: 0, drags: 0 };
			const canvas = document.getElementById('canvas');
			const point = event => {
				const box = canvas.getBoundingClientRect();
				const scale = Math.min(box.width / 1152, box.height / 648);
				return {
					x: (event.clientX - box.left - (box.width - 1152 * scale) / 2) / scale,
					y: (event.clientY - box.top - (box.height - 648 * scale) / 2) / scale
				};
			};
			window.addEventListener('pointerdown', event => {
				if (event.target !== canvas || event.pointerType === 'mouse' || state.id !== -1) return;
				const pos = point(event);
				if (pos.x < 24 || pos.x > 188 || pos.y < 462 || pos.y > 626) return;
				Object.assign(state, pos);
				state.id = event.pointerId;
				state.starts++;
			}, true);
			window.addEventListener('pointermove', event => {
				if (event.pointerId !== state.id) return;
				Object.assign(state, point(event));
				state.drags++;
			}, true);
			const release = event => {
				if (event.pointerId === state.id) state.id = -1;
			};
			window.addEventListener('pointerup', release, true);
			window.addEventListener('pointercancel', release, true);
			window.addEventListener('blur', () => { state.id = -1; });
			document.addEventListener('visibilitychange', () => {
				if (document.hidden) state.id = -1;
			});
		}
	""", true)
	web_stick = JavaScriptBridge.get_interface("mechanicStick")
	if web_stick != null:
		web_stick.id = -1
		web_stick.starts = 0
		web_stick.drags = 0

func setup_sprite() -> void:
	var atlas := preload("res://assets/characters/mechanic_directions.png")
	var frames := SpriteFrames.new()
	for index in range(8):
		var idle := StringName("idle_%d" % index)
		var walk := StringName("walk_%d" % index)
		frames.add_animation(idle)
		frames.add_animation(walk)
		frames.set_animation_speed(walk, 4.5)
		for column in [0] + WALK_COLUMNS:
			var frame := AtlasTexture.new()
			frame.atlas = atlas
			frame.region = Rect2(Vector2(column, ATLAS_ROWS[index]) * FRAME_SIZE, FRAME_SIZE)
			frame.filter_clip = true
			frames.add_frame(idle if column == 0 else walk, frame)
	sprite.sprite_frames = frames
	sprite.centered = false
	sprite.offset = -Vector2(FRAME_SIZE.x / 2, FRAME_SIZE.y)
	sprite.scale = Vector2(2.7, 2.7) if is_apartment() else Vector2.ONE
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	player.add_child(sprite)
	sprite.play("idle_2")

func style_hud_button(button: Button, normal: String, disabled: String) -> void:
	button.add_theme_font_size_override("font_size", 21)
	button.add_theme_color_override("font_disabled_color", Color("#bbada4"))
	for state in ["normal", "hover", "pressed", "disabled"]:
		var box := StyleBoxTexture.new()
		box.texture = load("res://assets/phone/%s.png" % (disabled if state == "disabled" else normal))
		box.content_margin_left = 48
		if state == "hover":
			box.modulate_color = Color(1.12, 1.12, 1.12)
		elif state == "pressed":
			box.modulate_color = Color(0.87, 0.87, 0.87)
		button.add_theme_stylebox_override(state, box)

func configure() -> void:
	match room_id:
		"apartment", "departure":
			target = Rect2(1179, 245, 110, 44)
			furniture = [Rect2(137, 233, 320, 211), Rect2(710, 230, 235, 204)]
		"street":
			target = Rect2(1100 if has_job else 715, 260, 205, 110)
		"kitchen":
			target = Rect2(770, 310, 150, 112)
			furniture = [Rect2(410, 165, 270, 110), Rect2(1100, 535, 245, 90)]
		"district":
			target = Rect2(695, 300, 145, 70)
			furniture = [Rect2(160, 215, 270, 105), Rect2(1035, 490, 230, 85)]
	if not is_apartment():
		furniture.append(target)

func _draw() -> void:
	if is_apartment():
		draw_texture_rect(preload("res://assets/apartment.png"), Rect2(Vector2.ZERO, ROOM_SIZE), false)
		return
	draw_rect(Rect2(Vector2.ZERO, ROOM_SIZE), Color("#292e38") if room_id == "kitchen" else Color("#323038"))
	for y in range(32, int(ROOM_SIZE.y), 32):
		draw_line(Vector2(32, y), Vector2(1468, y), Color("#3c3e48"))
	for x in range(32, int(ROOM_SIZE.x), 32):
		draw_line(Vector2(x, 32), Vector2(x, 818), Color("#3c3e48"))
	for wall in WALLS:
		draw_rect(wall, Color("#161c26"))
	for obstacle in furniture:
		draw_rect(obstacle, Color("#516273"))
	draw_rect(target, Color("#80613d"))
	draw_rect(target, Color("#f1bb70"), false, 3)
	var object_name := {"street": "К «Ферме Бенуа»" if has_job else "В подъезд", "kitchen": "Rational SCC 61", "district": "Телефон"}
	draw_string(ThemeDB.fallback_font, target.position + Vector2(10, 34), object_name[room_id], HORIZONTAL_ALIGNMENT_LEFT, -1, 17)

func draw_stick() -> void:
	var center := Vector2(82, 82)
	stick.draw_circle(center, 74, Color(0.08, 0.10, 0.14, 0.85))
	stick.draw_arc(center, 74, 0, TAU, 48, Color("#8791a0"), 2)
	stick.draw_circle(center + stick_vector * 49, 22, Color("#d6a166"))

func _input(event: InputEvent) -> void:
	if phone_visible:
		return
	if event is InputEventScreenTouch:
		if event.canceled or not event.pressed:
			if event.index == stick_id:
				reset_stick()
		elif has_phone_menu() and Rect2(phone.position, phone.size).has_point(event.position):
			get_viewport().set_input_as_handled()
			phone_opened.emit()
		elif Rect2(action.position, action.size).has_point(event.position) and in_reach():
			get_viewport().set_input_as_handled()
			interact()
		elif web_stick == null and stick_id == -1 and not mouse_stick and Rect2(stick.position, stick.size).has_point(event.position):
			stick_id = event.index
			touch_starts += 1
			update_stick(event.position)
			get_viewport().set_input_as_handled()
	elif event is InputEventScreenDrag and event.index == stick_id:
		touch_drags += 1
		update_stick(event.position)
		get_viewport().set_input_as_handled()

	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.device != InputEvent.DEVICE_ID_EMULATION:
		if event.pressed and stick_id == -1 and Rect2(stick.position, stick.size).has_point(event.position):
			mouse_stick = true
			update_stick(event.position)
			get_viewport().set_input_as_handled()
		elif not event.pressed and mouse_stick:
			reset_stick()
			get_viewport().set_input_as_handled()
	elif event is InputEventMouseMotion and mouse_stick:
		update_stick(event.position)
		get_viewport().set_input_as_handled()

func update_stick(position_on_screen: Vector2) -> void:
	var center := stick.position + stick.size * 0.5
	stick_vector = ((position_on_screen - center) / 49.0).limit_length()
	stick.queue_redraw()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and is_instance_valid(stick):
		reset_stick()

func reset_stick() -> void:
	mouse_stick = false
	stick_id = -1
	stick_vector = Vector2.ZERO
	stick.queue_redraw()

func _unhandled_key_input(event: InputEvent) -> void:
	if phone_visible:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_E:
			interact()
		elif event.physical_keycode == KEY_TAB and has_phone_menu():
			phone_opened.emit()

func _process(delta: float) -> void:
	if phone_visible:
		if web_stick != null:
			web_stick.id = -1
		sprite.play("idle_%d" % facing)
		return
	var keyboard := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if keyboard == Vector2.ZERO:
		keyboard = Vector2(
			int(Input.is_physical_key_pressed(KEY_D)) - int(Input.is_physical_key_pressed(KEY_A)),
			int(Input.is_physical_key_pressed(KEY_S)) - int(Input.is_physical_key_pressed(KEY_W))
		).limit_length()
	var web_active: bool = web_stick != null and int(web_stick.id) != -1
	if web_active:
		update_stick(Vector2(float(web_stick.x), float(web_stick.y)))
	elif web_stick != null and stick_id == -1 and not mouse_stick and stick_vector != Vector2.ZERO:
		reset_stick()
	var direction := stick_vector if web_active or stick_id >= 0 or mouse_stick else keyboard
	var moving := direction.length() > 0.2
	if moving:
		facing = posmod(roundi(direction.angle() / (PI / 4.0)), 8)
	var previous_position := player.position
	if moving:
		var step := Vector2.from_angle(facing * PI / 4.0) * SPEED * minf(delta, 0.05)
		move_axis(Vector2(step.x, 0.0))
		move_axis(Vector2(0.0, step.y))
	if is_instance_valid(diagnostics):
		travel += player.position.distance_to(previous_position)
		var starts := int(web_stick.starts) if web_stick != null else touch_starts
		var drags := int(web_stick.drags) if web_stick != null else touch_drags
		diagnostics.text = "Касания: %d   Сдвиги: %d   Путь: %.0f" % [starts, drags, travel]
	var walking := not player.position.is_equal_approx(previous_position)
	sprite.flip_h = facing in [3, 4, 5]
	var animation := StringName(("walk_%d" if walking else "idle_%d") % facing)
	if sprite.animation != animation:
		sprite.play(animation)
	update_hud()

func move_axis(step: Vector2) -> void:
	var destination := player.position + step
	for obstacle in obstacles:
		var bounds := obstacle.grow(PLAYER_RADIUS)
		if bounds.has_point(destination):
			# Allow leaving an overlap when restoring a position from an older build.
			if not bounds.has_point(player.position):
				return
			if destination.distance_squared_to(bounds.get_center()) <= player.position.distance_squared_to(bounds.get_center()):
				return
	player.position = destination

func in_reach() -> bool:
	return player.position.distance_to(player.position.clamp(target.position, target.end)) <= REACH

func update_hud() -> void:
	var location := {"apartment": "Квартира на Рубинштейна", "departure": "Квартира на Рубинштейна", "street": "Улица Рубинштейна", "kitchen": "Кухня «Фермы Бенуа»", "district": "Комната в спальном районе"}
	var task := {"apartment": "Выйти на улицу", "departure": "Выйти на улицу", "street": "Поехать на заявку" if has_job else "Вернуться в квартиру", "kitchen": "Осмотреть аппарат", "district": "Проверить телефон"}
	var ready := in_reach()
	prompt.text = "%s  ·  %s" % [location[room_id], task[room_id]]
	action.text = task[room_id] if ready else "Взаимодействие"
	action.tooltip_text = "Взаимодействовать (E)" if ready else "Подойди ближе"
	action.disabled = not ready

func interact() -> void:
	if not phone_visible and in_reach():
		interacted.emit()
