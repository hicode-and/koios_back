const express = require('express');
const router = express.Router();
//const multer = require('../middleware/multer-config');

const robotCtrl = require('../controllers/robot');


router.get('/', robotCtrl.getStatus);
router.post('/cmd', robotCtrl.handleCmd);

module.exports = router;