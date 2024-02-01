var express = require('express');
var app = express();
var port = normalizePort(process.env.PORT || '3000');
app.use(express.static('public'))

function normalizePort(val) {
    var port = parseInt(val, 10);
     if (isNaN(port)) {
      return val;
    }
    if (port >= 0) {
      return port;
    }
    return false;
}

app.listen(port, () => console.log(`Server listening on port: ${port}`));