local enabled = false

return {
  enable = function(self, config)
    if enabled then return end
    if config["lobby-map-descriptions"] == true then
      require("lobby-description").enable()
    end
    if config["clear-unique-building-preview"] == true then
      require("unique-placement").enable()
    end
    if config["building-preview-during-camera-movement"] == true then
      require("camera-preview").enable()
    end
    if config["distinct-dead-tree-sprites"] == true then
      require("dead-tree-sprites").enable()
    end
    if config["tower-door-height"] == true then
      require("tower-door-height").enable()
    end
    if config["lobby-load"] == true then
      require("lobby-load").enable()
    end
    if config["cliff-texture-direction"] == true then
      require("cliff-texture-direction").enable()
    end
    enabled = true
  end,
  disable = function()
    error("Interface and Visual Fixes requires a game restart to disable")
  end,
}
