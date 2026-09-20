-- Resolve native capabilities once through UCP's existing AOB cache.
-- No edition-specific VA/RVA fallback. See docs/native-integration-audit.md.
local P = {
  ProcessHeap = "8B 1D ? ? ? ? FF D3 50 FF 15 ? ? ? ? 8B F0 85 F6 75 0D",
  ReallocateHeap = "FF 15 ? ? ? ? 3B C7 75 04 33 C0 EB 78 83 05 ? ? ? ? 10 8B 35 ? ? ? ?",
  PlacementEntry = "83 EC 08 53 55 8B 6C 24 18 56 8B F1 8B 4C 24 24",
  PlacementNotifyCall = "53 B9 ? ? ? ? E8 ? ? ? ? 8B 44 24 2C 83 F8 05 7F 07",
  MinimapNotify = "83 79 38 00 75 11 C7 41 34 00 00 00 00 C7 41 38 02 00 00 00 C2 04 00 C7 41 38 01 00 00 00 C2 04 00",
  PlacementCommandReturn = "50 51 B9 ? ? ? ? 74 06 8B 15 ? ? ? ? 52 E8 ? ? ? ? 5E C3",
  CameraPreviewBranch = "39 1D ? ? ? ? 0F 85 ? ? ? ? 8B 3D ? ? ? ? 8B 2D ? ? ? ?",
  TreeFrameLoad = "69 F6 9C 00 00 00 0F BF 86 ? ? ? ? 85 C0 8B 96 ? ? ? ? 8B 0C 85 ? ? ? ?",
  LobbyLoadAction = "E8 ? ? ? ? 83 F8 02 7C AE BE 01 00 00 00 6A 09 B9 ? ? ? ? 89 35 ? ? ? ? E8 ? ? ? ?",
  LobbyPrepare = "C7 05 ? ? ? ? 03 00 00 00 89 35 ? ? ? ? 89 35 ? ? ? ? 89 35 ? ? ? ? 89 35 ? ? ? ? E8 ? ? ? ? 68 ? ? ? ?",
  TowerDoorCall1 = "DC 52 50 6A 36 B9 ? ? ? ? E8 ? ? ? ? 8B 86 ? ? ? ? 85 C0 0F 84 ? ? ? ? 83 C7 8F 57 83 C5 20",
  TowerDoorCall2 = "DC 52 50 6A 36 B9 ? ? ? ? E8 ? ? ? ? 8B 86 ? ? ? ? 85 C0 0F 84 ? ? ? ? 83 C7 89 57 83 C5 2E",
  TowerDoorCall3 = "CC 52 50 6A 36 B9 ? ? ? ? E8 ? ? ? ? 8B 86 ? ? ? ? 85 C0 0F 84 ? ? ? ? 83 C7 83 57 83 C5 30",
  TowerDoorCall4 = "CD 52 50 6A 36 B9 ? ? ? ? E8 ? ? ? ? 8B 86 ? ? ? ? 85 C0 0F 84 ? ? ? ? 83 C7 84 57 83 C5 31",
  TowerDoorCall5 = "03 D5 52 51 50 B9 ? ? ? ? E8 ? ? ? ? 66 83 BE ? ? ? ? 31 75 0A B9 ? ? ? ? E8 ? ? ? ? 5F 5E",
  RenderMapEntry = "83 EC 64 A1 ? ? ? ? 53 55 56 8B D9 57 33 FF 33 F6",
  FoundationDrawCall = "E8 ? ? ? ? 83 7C 24 54 00 74 34 A1 ? ? ? ? 2B 05 ? ? ? ? 8B 0D ? ? ? ? 8D 54 08 09",
  BuildingRefresh = "89 9C 0F 94 02 00 00 7E 7E EB 0F 83 F8 06 75 78 89 44 24 14 EB E2",
  BuildingRefreshTile = "03 81 28 E0 18 00 8B 04 85 ? ? ? ? A9 00 01 00 00 74 1C A8 02 75 18 A9 00 02 00 00 75 11",
  MapReset = "51 A1 ? ? ? ? 53 55 8B 2D ? ? ? ? 56 89 44 24 0C",
  TowerFoundationSelect = "66 89 84 51 E0 80 0C 00 EB 6A 8B 95 1C FF FF FF 8B 82 08 49 55 00 8B 0D ? ? ? ? 8D 54 01 FF",
  DrawBuildingOverlay = "8B 54 24 08 56 8B 74 24 08 8B 04 B5 ? ? ? ? 69 F6 58 14 00 00 8B B4 0E 30 05 00 00 8D 44 10 FF",
  DrawCliff = "55 8B EC 83 EC 18 A1 ? ? ? ? 8B 0D ? ? ? ? 89 45 F0 89 45 F8",
  CliffSelector = "8B 91 9C 48 55 00 85 D2 75 1B 83 F8 01 75 3E 8B 54 24 18 83 E2 1F BE 20 00 00 00 2B F2 89 B1 08 49 55 00 EB 38 83 FA 04 75 10 83 F8 01 75 10 8B 54 24 18 83 E2 1F 03 D0 EB 1D 83 FA 02 75 0E 83 E6 1F 83 C6 01 89 B1 08 49 55 00 EB 10 83 E6 1F BA 20 00 00 00 2B D6 89 91 08 49 55 00",
  CliffSource = "A1 ? ? ? ? 8B 14 85 ? ? ? ? 01 55 F0 A1 ? ? ? ? 8B 14 85 ? ? ? ? 01 55 F8 39 0D ? ? ? ?",
  CliffOffsetSource = "8B 15 ? ? ? ? 8B 04 95 ? ? ? ? 01 45 EC 8B 15 ? ? ? ? 8B 04 95 ? ? ? ? 01 45 FC 39 0D ? ? ? ?",
  ImageHeaders = "0F BF 90 ? ? ? ? 8B 46 04 03 44 24 10 51 8B 0E 52 03 CB",
  ImageSizes = "C2 0C 00 CC CC 8B 44 24 04 8B 14 85 ? ? ? ? 8B 04 85 ? ? ? ? 52 50 E8 ? ? ? ? C2 04 00",
  OverlayVerticalOffset = "89 1D ? ? ? ? A3 ? ? ? ? E8 ? ? ? ? A1 ? ? ? ? 50 B9 ? ? ? ? E8 ? ? ? ?",
  CliffWidth = "A1 ? ? ? ? 03 C0 03 F8 8B 45 FC BA B0 1F 00 00 F7 E2 03 F8",
  CliffFace = "03 F8 8B 55 F4 83 FA 00 0F 8E ? ? ? ? A1 ? ? ? ? 83 F8 01 0F 84 ? ? ? ? 83 F8 02 0F 84 ? ? ? ? 83 F8 03 0F 84 ? ? ? ? 8B 06 8B 5E 04 8B 4E 08",
  Buildings = "89 90 ? ? ? ? 66 83 B8 ? ? ? ? FF 75 22 51 B9 ? ? ? ? E8 ? ? ? ? 8B 0D ? ? ? ?",
  TileLogic = "F7 04 85 ? ? ? ? 00 00 00 10 89 74 24 18 89 5C 24 1C 89 7C 24 4C 89 54 24 48 74 05 83 44 24 60 0A",
  GameMode = "83 3D ? ? ? ? 06 75 34 8D 44 24 20 50 8D 4C 24 18 51 68 94 00 00 00",
  TextureRenderer = "B9 ? ? ? ? C7 05 ? ? ? ? 00 00 00 00 E8 ? ? ? ? C7 05 ? ? ? ? 00 00 00 00 FF 15 ? ? ? ? A3 ? ? ? ? C3",
  TileRows = "8B 04 BD ? ? ? ? C1 FA 03 03 C2 F7 04 85 ? ? ? ? 00 00 00 10 89 74 24 18 89 5C 24 1C 89 7C 24 4C",
  PreviewWidth = "A3 ? ? ? ? 7D 0B 89 1D ? ? ? ? 5B 83 C4 08 C3 8B 0D ? ? ? ?",
  LeftHeld = "83 3D ? ? ? ? 00 C7 05 ? ? ? ? 01 00 00 00 75 13 83 3D ? ? ? ? 00 75 0A C7 05 ? ? ? ? FF FF FF FF C7 05 ? ? ? ? FF FF FF FF",
  LeftReleased = "39 35 ? ? ? ? 0F 84 ? ? ? ? 39 35 ? ? ? ? 0F 84 ? ? ? ? A1 ? ? ? ? 3B C6 89 35 ? ? ? ?",
  LocalPlayer = "A1 ? ? ? ? 8B 54 24 20 69 C0 F4 39 00 00 01 90 ? ? ? ? 8D 80 ? ? ? ? 8B 44 24 28 50",
  LobbyLoadDraw = "83 3D ? ? ? ? 63 0F 84 89 02 00 00 39 2D ? ? ? ? 0F 84 6A 03 00 00",
  LobbyLoadItem = "03 00 00 02 BC 01 00 00 1C 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 AB 01 00 40 03 00 00 00 00 00 00 00 49 01 00 00",
}
P.CameraPreview = P.CameraPreviewBranch
P.CameraPreviewExit = "E8 ? ? ? ? 5E 5F 5D 5B 83 C4 08 C3 8D 49 00"

local A = {}
local bindings = {}
local function scan(name)
  local ok, address = pcall(core.AOBScan, P[name])
  if not ok or not address then
    error("Interface and Visual Fixes: unsupported or occupied native capability " .. name)
  end
  return address
end

bindings.ProcessHeap = function() return core.readInteger(scan("ProcessHeap") + 2) end
bindings.AllocateHeap = function() return core.readInteger(scan("ProcessHeap") + 11) end
bindings.ReallocateHeap = function() return core.readInteger(scan("ReallocateHeap") + 2) end
bindings.PlacementEntry = function() return scan("PlacementEntry") end
bindings.PlacementNotifyCall = function() return scan("PlacementNotifyCall") + 6 end
bindings.MinimapNotify = function() return scan("MinimapNotify") end
bindings.PlacementCommandReturn = function() return scan("PlacementCommandReturn") + 21 end
bindings.CameraPreviewBranch = function() return scan("CameraPreviewBranch") + 6 end
bindings.CameraPreviewExit = function() return A.CameraPreviewBranch + 6 + core.readInteger(A.CameraPreviewBranch + 2) end
bindings.TreeFrameLoad = function() return scan("TreeFrameLoad") + 15 end
bindings.LobbyLoadDraw = function() return scan("LobbyLoadDraw") end
bindings.LobbyLoadAction = function() return scan("LobbyLoadAction") + 5 end
bindings.LobbyLoadReject = function() return A.LobbyLoadAction + 5 - 0x52 end
bindings.LobbyPrepare = function() return scan("LobbyPrepare") end
bindings.TowerDoorCall1 = function() return scan("TowerDoorCall1") + 10 end
bindings.TowerDoorCall2 = function() return scan("TowerDoorCall2") + 10 end
bindings.TowerDoorCall3 = function() return scan("TowerDoorCall3") + 10 end
bindings.TowerDoorCall4 = function() return scan("TowerDoorCall4") + 10 end
bindings.TowerDoorCall5 = function() return scan("TowerDoorCall5") + 10 end
bindings.RenderMapEntry = function() return scan("RenderMapEntry") end
bindings.RenderMapResume = function() return A.RenderMapEntry + 8 end
bindings.FoundationDrawCall = function() return scan("FoundationDrawCall") end
bindings.BuildingRefresh = function() return scan("BuildingRefresh") end
bindings.BuildingRefreshResume = function() return A.BuildingRefresh + 7 end
bindings.BuildingRefreshTile = function() return scan("BuildingRefreshTile") + 6 end
bindings.BuildingRefreshTileResume = function() return A.BuildingRefreshTile + 7 end
bindings.MapReset = function() return scan("MapReset") end
bindings.MapResetResume = function() return A.MapReset + 6 end
bindings.TowerFoundationSelect = function() return scan("TowerFoundationSelect") + 10 end
bindings.TowerFoundationOriginal = function() return A.TowerFoundationSelect + 6 end
bindings.TowerFoundationResume = function() return A.TowerFoundationSelect + 106 end
bindings.DrawBuildingOverlay = function() return scan("DrawBuildingOverlay") end
bindings.DrawCliff = function() return scan("DrawCliff") end
bindings.CliffSelector = function() return scan("CliffSelector") end
bindings.CliffSelectorFallback = function() return A.CliffSelector + 93 end
bindings.CliffSelectorReturn = function() return A.CliffSelector + 100 end
bindings.CliffSource = function() return scan("CliffSource") end
bindings.CliffOffsetSource = function() return scan("CliffOffsetSource") end
bindings.LobbyLoadItem = function() return scan("LobbyLoadItem") end
bindings.LobbyLoadX = function() return A.LobbyLoadItem + 4 end
bindings.LobbyLoadY = function() return A.LobbyLoadItem + 8 end
bindings.LobbyLoadActive = function() return A.LobbyLoadItem + 24 end
bindings.LobbyLoadTexture = function() return A.LobbyLoadItem + 32 end
bindings.LobbyLoadTextureFrame = function() return A.LobbyLoadItem + 36 end
bindings.LobbyLoadTooltip = function() return A.LobbyLoadItem + 44 end
bindings.ImageHeaders = function() return core.readInteger(scan("ImageHeaders") + 3) end
bindings.ImageSizes = function() return core.readInteger(scan("ImageSizes") + 12) end
bindings.ImageOffsets = function() return core.readInteger(A.CliffSource + 8) end
bindings.CliffImages = function() return core.readInteger(A.DrawBuildingOverlay + 12) + 9*4 end
bindings.WallImages = function() return core.readInteger(A.DrawBuildingOverlay + 12) + 10*4 end
bindings.TowerImages = function() return core.readInteger(A.DrawBuildingOverlay + 12) + 54*4 end
bindings.OverlayVerticalOffset = function() return core.readInteger(scan("OverlayVerticalOffset") + 2) end
bindings.SecondaryImage = function() return core.readInteger(A.CliffSource + 16) end
bindings.PrimaryImage = function() return core.readInteger(A.CliffSource + 1) end
bindings.CliffWidth = function() return core.readInteger(scan("CliffWidth") + 1) end
bindings.CliffFace = function() return core.readInteger(scan("CliffFace") + 15) end
bindings.OverlayGm = function() return core.readInteger(scan("OverlayVerticalOffset") + 7) end
bindings.RenderMapState = function() return core.readInteger(A.RenderMapEntry + 4) end
bindings.Buildings = function() return core.readInteger(scan("Buildings") + 2) end
bindings.BuildingKind = function() return A.Buildings + 0xD2 end
bindings.BuildingId = function() return A.Buildings + 0xD8 end
bindings.BuildingX = function() return A.Buildings + 0xEE end
bindings.BuildingY = function() return A.Buildings + 0xF0 end
bindings.BuildingTile = function() return A.Buildings + 0xF4 end
bindings.BuildingState = function() return A.Buildings + 0xF8 end
bindings.CameraScrolling = function() return core.readInteger(A.CameraPreviewBranch - 4) end
bindings.LobbyMode = function() return core.readInteger(A.LobbyLoadDraw + 2) end
bindings.TileLogic = function() return core.readInteger(scan("TileLogic") + 3) end
bindings.TileBuilding = function() return A.TileLogic - 0x165160 + 0x2029B0 end
bindings.TileHeight = function() return A.TileLogic - 0x165160 + 0x29FA30 end
bindings.TileTerrain = function() return A.TileLogic - 0x165160 + 0x2B3440 end
bindings.MapOrientation = function() return A.TileLogic - 0x165160 + 0x55489C end
bindings.GameMode = function() return core.readInteger(scan("GameMode") + 2) end
bindings.TextureRenderer = function() return core.readInteger(scan("TextureRenderer") + 1) end
bindings.ImageData = function() return A.TextureRenderer + 0x78 end
bindings.CursorSamplePointer = function() return A.ViewportY - 8 end
bindings.ViewportY = function() return core.readInteger(A.MapReset + 2) end
bindings.TileRows = function() return core.readInteger(scan("TileRows") + 3) end
bindings.PreviewWidth = function() return core.readInteger(scan("PreviewWidth") + 1) end
bindings.LeftHeld = function() return core.readInteger(scan("LeftHeld") + 2) end
bindings.LeftReleased = function() return core.readInteger(scan("LeftReleased") + 2) end
bindings.LocalPlayer = function() return core.readInteger(scan("LocalPlayer") + 1) end
bindings.TreeFrame = function() return core.readInteger(A.TreeFrameLoad + 2) end
bindings.TreeStage = function() return A.TreeFrame + 0x80 end
bindings.TreeFelling = function() return A.TreeFrame + 0x76 end
bindings.TreeKind = function() return A.TreeFrame + 0x46 end

setmetatable(A, {__index = function(self, name)
  local resolve = bindings[name]
  if not resolve then return nil end
  local address = resolve()
  rawset(self, name, address)
  return address
end})
local M = {addresses = A, patterns = P}
-- Use the framework's symbol mapping. Limit declarations to symbols used by
-- this wrapper because UCP 3.0.7 gives FASM a 64 KB workspace.
local function operands(script)
  local used = {}
  for name in script:gmatch("[%a_][%w_]*") do
    if A[name] then used[name] = A[name] end
  end
  return used
end
function M.allocateAssembly(script)
  return core.allocateAssembly(script, operands(script))
end
function M.assemble(script, origin)
  return core.assemble(script, operands(script), origin)
end

-- Preflight every enabled binding before any feature installs its patches.
local required = {
  ["clear-unique-building-preview"] = {
    "PlacementEntry", "PlacementNotifyCall", "MinimapNotify", "PlacementCommandReturn", "GameMode",
    "LocalPlayer",
  },
  ["building-preview-during-camera-movement"] = {
    "CameraPreviewBranch", "CameraPreviewExit", "PreviewWidth", "LeftHeld", "LeftReleased",
  },
  ["distinct-dead-tree-sprites"] = {
    "TreeFrameLoad", "TreeFrame", "TreeStage", "TreeFelling", "TreeKind",
  },
  ["tower-door-height"] = {
    "TowerDoorCall1", "TowerDoorCall2", "TowerDoorCall3", "TowerDoorCall4", "TowerDoorCall5",
    "RenderMapEntry", "RenderMapResume", "FoundationDrawCall", "BuildingRefresh", "BuildingRefreshResume",
    "BuildingRefreshTile", "BuildingRefreshTileResume", "MapReset", "MapResetResume", "TowerFoundationSelect",
    "TowerFoundationOriginal", "TowerFoundationResume", "DrawBuildingOverlay", "DrawCliff", "ImageHeaders",
    "WallImages", "TowerImages", "OverlayVerticalOffset", "CliffWidth", "CliffFace",
    "OverlayGm", "RenderMapState", "Buildings", "BuildingKind", "BuildingId",
    "BuildingX", "BuildingY", "BuildingTile", "BuildingState", "TileLogic",
    "TileBuilding", "TileHeight", "TileTerrain", "MapOrientation", "TextureRenderer",
    "CursorSamplePointer", "ViewportY", "TileRows",
  },
  ["lobby-load"] = {
    "LobbyLoadDraw", "LobbyLoadAction", "LobbyLoadReject", "LobbyPrepare", "LobbyLoadItem",
    "LobbyLoadX", "LobbyLoadY", "LobbyLoadActive", "LobbyLoadTexture", "LobbyLoadTextureFrame",
    "LobbyLoadTooltip", "LobbyMode", "GameMode",
  },
  ["cliff-texture-direction"] = {
    "ProcessHeap", "AllocateHeap", "ReallocateHeap", "RenderMapEntry", "RenderMapResume",
    "CliffSelector", "CliffSelectorFallback", "CliffSelectorReturn", "CliffSource", "CliffOffsetSource",
    "ImageHeaders", "ImageSizes", "ImageOffsets", "CliffImages", "SecondaryImage",
    "PrimaryImage", "RenderMapState", "TileLogic", "TileHeight", "TileTerrain",
    "ImageData", "TileRows",
  },
}
function M.prepare(config)
  for option, names in pairs(required) do
    if config[option] == true then
      for _, name in ipairs(names) do assert(A[name], name) end
    end
  end
  local function expect(actual, expected, capability)
    if actual ~= expected then
      error("Interface and Visual Fixes: inconsistent or occupied native capability " .. capability)
    end
  end
  local function callTarget(site) return site + 5 + core.readInteger(site + 1) end
  if config["clear-unique-building-preview"] == true then
    expect(callTarget(A.PlacementNotifyCall), A.MinimapNotify, "placement notification")
    expect(callTarget(A.PlacementCommandReturn - 5), A.PlacementEntry, "placement command")
  end
  if config["building-preview-during-camera-movement"] == true then
    expect(A.CameraPreviewExit, scan("CameraPreviewExit") + 6, "camera exit")
  end
  if config["lobby-load"] == true then
    expect(core.readInteger(A.LobbyPrepare + 2), A.GameMode, "lobby preparation")
  end
  if config["tower-door-height"] == true then
    for i = 1, 5 do
      expect(callTarget(A["TowerDoorCall" .. i]), A.DrawBuildingOverlay, "tower overlay")
    end
    expect(callTarget(A.FoundationDrawCall), A.DrawCliff, "tower foundation")
  end
  if config["cliff-texture-direction"] == true then
    expect(core.readInteger(A.CliffSource + 23), A.ImageOffsets, "secondary cliff offsets")
    expect(core.readInteger(A.CliffOffsetSource + 2), A.PrimaryImage, "offset cliff primary image")
    expect(core.readInteger(A.CliffOffsetSource + 18), A.SecondaryImage, "offset cliff secondary image")
    expect(core.readInteger(A.CliffOffsetSource + 9), A.ImageOffsets, "offset cliff primary offsets")
    expect(core.readInteger(A.CliffOffsetSource + 25), A.ImageOffsets, "offset cliff secondary offsets")
  end
end
return M
