const express = require('express');
const router = express.Router();
const ChatController = require('../controllers/chatController');

router.post('/', ChatController.handleChat);

module.exports = router;
