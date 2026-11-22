const { getChatResponse } = require('../services/chatBotService');
const { successResponse, errorResponse } = require('../utils/response');

class ChatController {
  static async handleChat(req, res) {
    try {
      const { message, history, language } = req.body;

      if (!message || message.trim() === '') {
        return errorResponse(res, 'Please provide a message or question.', 400);
      }

      const reply = await getChatResponse({
        message,
        history: history || [],
        language: language || (req.user ? req.user.language : 'en')
      });

      return successResponse(res, {
        reply,
        timestamp: new Date().toISOString()
      });
    } catch (err) {
      return errorResponse(res, 'The AI assistant is temporarily unavailable. Please try again.', 500, err);
    }
  }
}

module.exports = ChatController;
