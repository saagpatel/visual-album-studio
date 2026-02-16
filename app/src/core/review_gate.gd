extends RefCounted
class_name ReviewGate

var goal: String
var success_metrics: Array[String] = []
var must_items: Array[String] = []
var deferred_items: Array[String] = []
var stop_conditions: Array[String] = []
var verification_commands: Array[String] = []
