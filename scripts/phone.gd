extends ColorRect

signal accepted
signal declined
signal dismissed

const CREAM := Color("#f2dfbf")
const TEAL := Color("#83c5bb")

func setup(has_job: bool, time: String) -> void:
	color = Color("#17131abb")
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var frame := TextureRect.new()
	frame.texture = preload("res://assets/phone/phone.png")
	frame.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.position = Vector2(415, 22)
	frame.size = Vector2(322, 604)
	add_child(frame)

	var content := Control.new()
	content.position = Vector2(436, 70)
	content.size = Vector2(276, 500)
	content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(content)
	put_label(content, time, Rect2(10, 0, 100, 34), 20)
	var close := put_button(content, "", Rect2(234, -1, 43, 42), "close", dismissed.emit)
	close.tooltip_text = "Закрыть телефон (Esc)"
	put_label(content, "Женя", Rect2(0, 50, 276, 50), 32, CREAM, true)
	line_at(content, Vector2(9, 108), 258)

	var card := Panel.new()
	card.position = Vector2(0, 126)
	card.size = Vector2(276, 217)
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var box := StyleBoxFlat.new()
	box.bg_color = Color("#302e2d")
	box.border_color = Color("#62564c")
	box.set_border_width_all(2)
	box.set_corner_radius_all(7)
	card.add_theme_stylebox_override("panel", box)
	content.add_child(card)
	put_label(card, "Заявка №001", Rect2(0, 5, 276, 34), 21, TEAL, true)
	line_at(card, Vector2(14, 42), 248)
	var oven := TextureRect.new()
	oven.texture = preload("res://assets/phone/oven.png")
	oven.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	oven.position = Vector2(12, 51)
	oven.size = Vector2(96, 96)
	oven.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(oven)
	put_label(card, "«Ферма Бенуа»", Rect2(113, 66, 152, 29), 19)
	put_label(card, "Rational SCC 61", Rect2(113, 96, 152, 25), 17)
	line_at(card, Vector2(14, 151), 248)
	put_label(card, "Аппарат перестал греть.", Rect2(0, 159, 276, 45), 19, CREAM, true)
	if has_job:
		put_label(content, "Заявка принята", Rect2(0, 364, 276, 54), 23, TEAL, true)
	else:
		put_button(content, "Взяться за ремонт", Rect2(0, 363, 276, 54), "accept", accepted.emit)
		put_button(content, "Отказаться", Rect2(0, 427, 276, 54), "", declined.emit)

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode in [KEY_ESCAPE, KEY_TAB]:
			get_viewport().set_input_as_handled()
			dismissed.emit()

func put_label(parent: Control, value: String, rect: Rect2, font_size: int, tint: Color = CREAM, centered: bool = false) -> void:
	var label := Label.new()
	label.position = rect.position
	label.size = rect.size
	label.text = value
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	if centered:
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", tint)
	parent.add_child(label)

func line_at(parent: Control, start: Vector2, width: float) -> void:
	var line := ColorRect.new()
	line.position = start
	line.size = Vector2(width, 2)
	line.color = Color("#886d55")
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(line)

func put_button(parent: Control, value: String, rect: Rect2, asset: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = value
	button.position = rect.position
	button.size = rect.size
	button.focus_mode = Control.FOCUS_NONE
	button.add_theme_color_override("font_color", CREAM)
	button.add_theme_font_size_override("font_size", 21)
	for state in ["normal", "hover", "pressed"]:
		var style: StyleBox
		if asset.is_empty():
			var flat := StyleBoxFlat.new()
			flat.bg_color = Color("#493d38")
			flat.border_color = Color("#957d70")
			flat.set_corner_radius_all(7)
			flat.set_border_width_all(2)
			style = flat
		else:
			var texture_box := StyleBoxTexture.new()
			texture_box.texture = load("res://assets/phone/%s.png" % asset)
			style = texture_box
		button.add_theme_stylebox_override(state, style)
	button.pressed.connect(callback)
	parent.add_child(button)
	return button
