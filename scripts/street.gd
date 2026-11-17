extends Node2D

const GROUND = preload("res://assets/street/ground.png")
const OBJECTS = preload("res://assets/street/objects.png")
const TILE := 32
const ARRIVAL := Vector2(1248, 320)
const COURTYARD := Rect2(1216, 268, 64, 32)
const SERVICE_DOOR := Rect2(1200, 470, 56, 32)
const SOLIDS: Array[Rect2] = [
	Rect2(454, 80, 648, 201), # Restaurant
	Rect2(1070, 110, 143, 150), Rect2(1280, 110, 169, 150),
	Rect2(288, 174, 145, 99), # Shop
	Rect2(1140, 376, 178, 96), # Service annex
	Rect2(126, 258, 74, 28), Rect2(276, 258, 75, 28),
	Rect2(74, 351, 30, 26), Rect2(370, 446, 28, 24),
	Rect2(315, 350, 63, 22), Rect2(592, 332, 94, 28),
	Rect2(771, 303, 107, 19), Rect2(1326, 507, 110, 40)
]
const PROPS := [
	[Rect2(103, 0, 683, 209), Rect2(448, 72, 655, 210)],
	[Rect2(16, 212, 261, 121), Rect2(1068, 106, 382, 160)],
	[Rect2(496, 225, 166, 115), Rect2(284, 163, 154, 112)],
	[Rect2(693, 222, 176, 118), Rect2(1136, 363, 187, 112)],
	[Rect2(307, 232, 162, 104), Rect2(119, 166, 235, 121)],
	[Rect2(14, 333, 126, 111), Rect2(25, 235, 125, 148)],
	[Rect2(14, 333, 126, 111), Rect2(329, 317, 125, 155)],
	[Rect2(14, 333, 126, 111), Rect2(65, 438, 146, 166)],
	[Rect2(170, 344, 32, 100), Rect2(260, 344, 26, 79)],
	[Rect2(170, 344, 32, 100), Rect2(961, 484, 26, 79)],
	[Rect2(221, 393, 100, 51), Rect2(310, 320, 75, 52)],
	[Rect2(339, 362, 126, 82), Rect2(588, 297, 102, 65)],
	[Rect2(339, 362, 126, 82), Rect2(951, 295, 90, 58)],
	[Rect2(547, 386, 126, 58), Rect2(768, 275, 114, 48)],
	[Rect2(708, 374, 148, 70), Rect2(1321, 473, 119, 74)],
	[Rect2(493, 390, 27, 54), Rect2(452, 570, 17, 34)],
	[Rect2(493, 390, 27, 54), Rect2(514, 570, 17, 34)],
	[Rect2(493, 390, 27, 54), Rect2(1127, 570, 17, 34)]
]

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var tiles := TileMapLayer.new()
	var tile_set := TileSet.new()
	tile_set.tile_size = Vector2i(TILE, TILE)
	var source := TileSetAtlasSource.new()
	source.texture = GROUND
	source.texture_region_size = Vector2i(TILE, TILE)
	for index in range(13):
		source.create_tile(Vector2i(index, 0))
	tile_set.add_source(source, 0)
	tiles.tile_set = tile_set
	add_child(tiles)
	for y in range(27):
		for x in range(47):
			tiles.set_cell(Vector2i(x, y), 0, Vector2i(ground_tile(x, y), 0))

	for prop in PROPS:
		var region: Rect2 = prop[0]
		var placement: Rect2 = prop[1]
		var object := Sprite2D.new()
		var texture := AtlasTexture.new()
		texture.atlas = OBJECTS
		texture.region = region
		texture.filter_clip = true
		object.texture = texture
		object.centered = false
		object.position = placement.position
		object.scale = placement.size / region.size
		add_child(object)

func ground_tile(x: int, y: int) -> int:
	var crossing := x in [11, 12, 37, 38]
	if y == 19:
		return 10 if crossing else 7
	if y == 24:
		return 12 if crossing else 11
	if y > 19 and y < 24:
		if crossing:
			return 6
		if y == 21 and x % 4 == 1:
			return 5
		return 4 if (x * 7 + y * 3) % 13 == 0 else 3
	if x < 14 and y < 18:
		if x in [6, 7, 8] or y in [12, 13]:
			return 8
		return 9
	return (x + y * 2) % 3
