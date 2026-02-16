extends RefCounted
class_name VasIds

static var _counter: int = 0

static func new_id(prefix: String) -> String:
	_counter += 1
	var payload = "%s:%d:%d:%d" % [prefix, Time.get_ticks_usec(), _counter, randi()]
	var hash = HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(payload.to_utf8_buffer())
	var digest = hash.finish().hex_encode().substr(0, 16)
	return "%s_%s" % [prefix, digest]
