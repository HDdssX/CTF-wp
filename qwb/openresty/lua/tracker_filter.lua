-- tracker_filter.lua

local function bencode_error(msg)
    local key = "failure reason"
    return "d14:" .. key .. string.format("%d:%s", #msg, msg) .. "e"
end

local function reject(msg)
    ngx.status = 400
    ngx.header.content_type = "text/plain"
    ngx.say(bencode_error(msg or "Forbidden"))
    ngx.exit(ngx.status)
end

local common_browsers = {
    "Mozilla", "Chrome", "Safari", "Edge", "Firefox", "Opera", "Trident"
}

local function is_browser(ua)
    if not ua then return false end
    for _, keyword in ipairs(common_browsers) do
        if ua:find(keyword) then
            return true
        end
    end
    return false
end

local function is_valid_passkey(passkey)
    return type(passkey) == "string" and #passkey == 32
end

local function is_positive_integer(val)
    local num = tonumber(val)
    return num and num >= 0 and math.floor(num) == num
end

local function is_valid_port(val)
    local port = tonumber(val)
    return port and port >= 1 and port <= 65535 and math.floor(port) == port
end

local function main()
    local ua = ngx.var.http_user_agent
    if is_browser(ua) then
        return reject("Browser access blocked !")
    end

    if ngx.var.uri and ngx.var.uri:find("api/announce") then
        return reject("Not support, please use announce.php")
    end

    local args = ngx.req.get_uri_args()

    if args["auth_key"] then
        return reject("auth_key is not allowed")
    end

    if not is_valid_passkey(args["passkey"]) then
        return reject("Invalid or missing passkey")
    end

    local required_fields = {
        "info_hash",
        "peer_id",
        "port",
        "downloaded",
        "uploaded",
        "left"
    }

    for _, field in ipairs(required_fields) do
        if not args[field] then
            return reject("Missing parameter: " .. field)
        end
    end

    if not is_valid_port(args["port"]) then
        return reject("Invalid port")
    end

    for _, field in ipairs({"downloaded", "uploaded", "left"}) do
        if not is_positive_integer(args[field]) then
            return reject("Invalid value for " .. field)
        end
    end

    if args["event"] then
        local valid_events = {
            started = true,
            completed = true,
            stopped = true,
            paused = true
        }
        if not valid_events[args["event"]] then
            return reject("Invalid event")
        end
    end

end

return main
