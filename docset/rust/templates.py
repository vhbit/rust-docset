FEED_XML = """<entry>
    <version>{{ version }}/{{ time.strftime("%Y-%m-%d-%H-%M") }}</version>
    <sha1>{{ sha }}</sha1>
    <url>{{ base_url }}/{{ file_name|urlencode }}</url>
</entry>
"""

INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
   <plist version="1.0">
      <dict>
         <key>CFBundleIdentifier</key>
         <string>{{ bundle_id }}</string>
         <key>CFBundleName</key>
         <string>{{ name }}</string>
         <key>dashIndexFilePath</key><string>index.html</string>
         <key>DocSetPlatformFamily</key>
         <string>rust</string>
         <key>isDashDocset</key><true/>
         <key>isJavaScriptEnabled</key><true/>
         <key>DashDocSetFamily</key><string>dashtoc</string>
      </dict>
</plist>
"""
