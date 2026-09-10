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
    enabled = true
  end,
  disable = function()
    error("Interface and Visual Fixes requires a game restart to disable")
  end,
}
