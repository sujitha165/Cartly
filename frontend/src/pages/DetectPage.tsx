import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ImageUploader } from '../components/detection/ImageUploader';
import { ScanningAnimation } from '../components/detection/ScanningAnimation';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { useLanguage } from '../context/LanguageContext';
import { useToast } from '../context/ToastContext';
import { diseaseService } from '../services/diseaseService';
import { CROPS_LIST } from '../data/mockDiseases';
import { ScanLine, Sparkles, Info } from 'lucide-react';
import { ScanRecord } from '../types';

export const DetectPage: React.FC = () => {
  const { t } = useLanguage();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [cropType, setCropType] = useState('Tomato');
  const [symptoms, setSymptoms] = useState('');

  const [isScanning, setIsScanning] = useState(false);
  const [analyzedScan, setAnalyzedScan] = useState<ScanRecord | null>(null);

  const handleImageSelected = (file: File, previewUrl: string) => {
    if (!file.type.startsWith('image/')) {
      showToast('Please upload a valid image file.', 'error');
      return;
    }

    setSelectedFile(file);
    setImagePreview(previewUrl);
    setAnalyzedScan(null);
  };

  const handleImageRemoved = () => {
    setSelectedFile(null);
    setImagePreview(null);
    setAnalyzedScan(null);
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile) {
      showToast('Please upload a crop leaf image first.', 'error');
      return;
    }

    if (!selectedFile.type.startsWith('image/')) {
      showToast('Invalid file. Please upload an image.', 'error');
      return;
    }

    setIsScanning(true);
    setAnalyzedScan(null);

    try {
      const formData = new FormData();

      formData.append('image', selectedFile);
      formData.append('crop', cropType);
      formData.append('symptoms', symptoms);

      const result = await diseaseService.analyzeCropImage(formData);

      if (!result || !result.id || !result.disease) {
        throw new Error('Invalid diagnosis result received.');
      }

      setAnalyzedScan(result);
    } catch (err) {
      console.error('Analysis error:', err);

      setIsScanning(false);

      showToast(
        'Unable to analyze this image. Please upload a clear crop leaf image.',
        'error'
      );
    }
  };

  const handleAnimationComplete = () => {
    if (!analyzedScan) {
      setIsScanning(false);

      showToast(
        'Diagnosis could not be completed. Please try again.',
        'error'
      );

      return;
    }

    showToast('Diagnosis complete! Showing report.', 'success');

    navigate(`/results/${analyzedScan.id}`);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 dark:text-stone-100 tracking-tight">
            {t('detect.title')}
          </h1>

          <Badge
            variant="emerald"
            icon={<Sparkles className="w-3.5 h-3.5" />}
          >
            AI Diagnostic Vision
          </Badge>
        </div>

        <p className="text-xs sm:text-sm text-stone-500 dark:text-stone-400">
          {t('detect.subtitle')}
        </p>
      </div>

      {isScanning && imagePreview ? (
        <div className="bg-white dark:bg-darkbg-card border border-stone-200 dark:border-darkbg-border rounded-3xl p-6 sm:p-10 shadow-sm animate-fadeIn">
          <ScanningAnimation
            imagePreview={imagePreview}
            cropName={cropType}
            onComplete={handleAnimationComplete}
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-7 space-y-4">
            <ImageUploader
              selectedImage={selectedFile}
              imagePreview={imagePreview}
              onImageSelected={handleImageSelected}
              onImageRemoved={handleImageRemoved}
            />

            <div className="bg-agri-50/60 dark:bg-agri-950/30 border border-agri-200/70 dark:border-agri-800/60 rounded-2xl p-4 text-xs text-stone-600 dark:text-stone-300 space-y-2">
              <span className="font-bold text-agri-800 dark:text-agri-300 flex items-center gap-1.5">
                <Info className="w-4 h-4 text-agri-600 shrink-0" />
                Tips for Accurate Leaf Diagnosis:
              </span>

              <ul className="list-disc ml-5 space-y-1 text-stone-500 dark:text-stone-400">
                <li>
                  Capture the leaf under natural indirect sunlight.
                </li>
                <li>
                  Make sure the affected area is clearly visible.
                </li>
                <li>
                  Avoid blurry or very dark images.
                </li>
                <li>
                  Upload one clear crop leaf whenever possible.
                </li>
              </ul>
            </div>
          </div>

          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white dark:bg-darkbg-card border border-stone-200 dark:border-darkbg-border rounded-3xl p-6 shadow-xs space-y-5">
              <h3 className="font-bold text-base text-stone-900 dark:text-stone-100">
                Diagnostic Parameters
              </h3>

              <div>
                <label className="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1.5">
                  {t('detect.selectCrop')} *
                </label>

                <select
                  value={cropType}
                  onChange={e => setCropType(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-300 dark:border-darkbg-border bg-white dark:bg-darkbg-input text-stone-900 dark:text-stone-100 text-sm font-medium focus:ring-2 focus:ring-agri-500 focus:outline-none"
                >
                  {CROPS_LIST.map(crop => (
                    <option key={crop} value={crop}>
                      {crop}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1.5">
                  {t('detect.symptomsOptional')}
                </label>

                <textarea
                  rows={3}
                  value={symptoms}
                  onChange={e => setSymptoms(e.target.value)}
                  placeholder={t('detect.symptomsPlaceholder')}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-300 dark:border-darkbg-border bg-white dark:bg-darkbg-input text-stone-900 dark:text-stone-100 text-xs sm:text-sm placeholder-stone-400 focus:ring-2 focus:ring-agri-500 focus:outline-none"
                />
              </div>

              <div className="pt-2">
                <Button
                  type="button"
                  size="lg"
                  disabled={!selectedFile || isScanning}
                  onClick={handleStartAnalysis}
                  className="w-full font-bold shadow-lg"
                  icon={<ScanLine className="w-5 h-5" />}
                >
                  {isScanning
                    ? 'Analyzing...'
                    : t('detect.analyzeBtn')}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};