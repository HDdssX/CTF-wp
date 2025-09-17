const express = require('express');
const ejs = require('ejs');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = parseInt(process.env.PORT) || 3000;

app.set('view engine', 'ejs');
app.use(express.json({
    limit: '1mb'
}));

const STATIC_DIR = path.join(__dirname, '/');


// serve index for better viewing
function serveIndex(req, res) {
    var templ = req.query.templ || 'index';
    var lsPath = path.join(__dirname, req.path);
    try {
        res.render(templ, {
            filenames: fs.readdirSync(lsPath),
            path: req.path
        });
    } catch (e) {
        console.log(e);
        res.status(500).send('Error rendering page');
    }
}


// static serve for simply view/download
app.use(express.static(STATIC_DIR));


// Security middleware
app.use((req, res, next) => {
    if (typeof req.path !== 'string' || 
            (typeof req.query.templ !== 'string' && typeof req.query.templ !== 'undefined')
        ) res.status(500).send('Error parsing path');
    else if (/js$|\.\./i.test(req.path)) res.status(403).send('Denied filename');
    else next();
})


// logic middleware
app.use((req, res, next) => {
    if (req.path.endsWith('/')) serveIndex(req, res);
    else next();
})


// Upload operation handler
app.put('/*', (req, res) => {
    const filePath = path.join(STATIC_DIR, req.path);

    if (fs.existsSync(filePath)) {
        return res.status(500).send('File already exists');
    }

    fs.writeFile(filePath, Buffer.from(req.body.content, 'base64'), (err) => {
        if (err) {
            return res.status(500).send('Error writing file');
        }
        res.status(201).send('File created/updated');
    });
});


// Server start
app.listen(PORT, () => {
    console.log(`Static server is running on http://localhost:${PORT}`);
});
