const ScanModel = require('../models/scanModel');
const NotificationModel = require('../models/notificationModel');
const { analyzeCropImage } = require('../services/aiDetectionService');
const { successResponse, errorResponse } = require('../utils/response');

class DiseaseController {
  static async analyze(req, res) {
    try {
      const { crop, symptoms, notes, imageUrl } = req.body;
      const file = req.file;

      // Determine image URL
      let finalImageUrl = imageUrl;
      if (file) {
        // Construct accessible static URL or local path
        finalImageUrl = `/uploads/${file.filename}`;
      } else if (!imageUrl) {
        // Provide sample image if neither uploaded nor linked
        finalImageUrl = 'https://images.unsplash.com/photo-1592417817098-8f3d6910985c?auto=format&fit=crop&w=800&q=80';
      }

      // Execute AI Analysis
      const analysisResult = await analyzeCropImage({
        imageBuffer: file ? file.buffer : null,
        imageUrl: finalImageUrl,
        cropType: crop || 'Tomato',
        symptoms: symptoms || '',
        fileName: file ? file.originalname : 'crop.jpg'
      });

      // Save to database/store linked to authenticated user
      const savedScan = await ScanModel.create({
        user_id: req.user ? req.user.id : 1,
        image_url: finalImageUrl,
        crop: analysisResult.crop,
        disease: analysisResult.disease,
        confidence: analysisResult.confidence,
        severity: analysisResult.severity,
        symptoms: analysisResult.symptoms,
        causes: analysisResult.causes,
        notes: notes || ''
      });

      // Trigger user notification
      if (req.user) {
        await NotificationModel.create({
          user_id: req.user.id,
          title: `Analysis: ${analysisResult.crop} - ${analysisResult.disease}`,
          message: `Detection confidence is ${analysisResult.confidence}% (${analysisResult.severity} severity). View action plan.`,
          type: 'scan',
          link: `/results/${savedScan.id}`
        });
      }

      return successResponse(
        res,
        {
          ...savedScan,
          pathogen: analysisResult.pathogen,
          treatment: analysisResult.treatment,
          prevention: analysisResult.prevention,
          monitoring: analysisResult.monitoring,
          expert_warning: analysisResult.expert_warning
        },
        'Crop image analyzed successfully.',
        201
      );
    } catch (err) {
      return errorResponse(res, 'We couldn\'t analyze this image. Please upload a clearer crop image.', 500, err);
    }
  }

  static async getHistory(req, res) {
    try {
      const userId = req.user.id;
      const { crop, severity, search, limit } = req.query;

      const scans = await ScanModel.getAllByUserId(userId, { crop, severity, search, limit });
      return successResponse(res, scans);
    } catch (err) {
      return errorResponse(res, 'Failed to fetch scan history.', 500, err);
    }
  }

  static async getById(req, res) {
    try {
      const { id } = req.params;
      const scan = await ScanModel.findById(id);

      if (!scan) {
        return errorResponse(res, 'Crop scan record not found.', 404);
      }

      // Reconstruct knowledge base treatment advice for this scan
      const { analyzeCropImage } = require('../services/aiDetectionService');
      const analysis = await analyzeCropImage({
        cropType: scan.crop,
        symptoms: scan.disease
      });

      return successResponse(res, {
        ...scan,
        pathogen: analysis.pathogen,
        treatment: analysis.treatment,
        prevention: analysis.prevention,
        monitoring: analysis.monitoring,
        expert_warning: analysis.expert_warning
      });
    } catch (err) {
      return errorResponse(res, 'Failed to retrieve scan report.', 500, err);
    }
  }

  static async deleteScan(req, res) {
    try {
      const { id } = req.params;
      const deleted = await ScanModel.deleteById(id, req.user.id);
      if (!deleted) {
        return errorResponse(res, 'Scan record not found or unauthorized to delete.', 404);
      }
      return successResponse(res, { id }, 'Scan record deleted successfully.');
    } catch (err) {
      return errorResponse(res, 'Failed to delete scan record.', 500, err);
    }
  }
}

module.exports = DiseaseController;
