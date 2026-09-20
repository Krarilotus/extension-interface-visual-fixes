local enabled = false
local features = {
  {"lobby-map-descriptions", "lobby-description"},
  {"clear-unique-building-preview", "unique-placement"},
  {"building-preview-during-camera-movement", "camera-preview"},
  {"distinct-dead-tree-sprites", "dead-tree-sprites"},
  {"tower-door-height", "tower-door-height"},
  {"lobby-load", "lobby-load"},
  {"cliff-texture-direction", "cliff-texture-direction"},
}

return {
  enable = function(self, config)
    if enabled then return end
    log(INFO, "startup diagnostics schema=1; begin")
    local active = {}
    for _, feature in ipairs(features) do
      if config[feature[1]] == true then
        active[#active+1] = feature
      end
    end
    if #active > 0 then require("native-layout").prepare(config) end
    for _, feature in ipairs(active) do
      log(INFO, "installing " .. feature[1])
      require(feature[2]).enable()
      log(INFO, "installed " .. feature[1])
    end
    enabled = true
    log(INFO, "startup complete; diagnostics are startup-only, not a crash dump")
  end,
  disable = function()
    error("Interface and Visual Fixes requires a game restart to disable")
  end,
}
