import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  BookmarkCheck,
  Calendar,
  Layers,
  ArrowLeft,
  ScanLine,
  FileCheck,
  Activity,
  HeartPulse,
  Leaf
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { ConfidenceMeter } from '../components/detection/ConfidenceMeter';
import { SeverityIndicator } from '../components/detection/SeverityIndicator';
import { useLanguage } from '../context/LanguageContext';
import { useToast } from '../context/ToastContext';
import { diseaseService } from '../services/diseaseService';
import { ScanRecord } from '../types';
import { formatDate, getSeverityStyles } from '../utils/formatters';

export const ResultPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { showToast } = useToast();

  const [scan, setScan] = useState<ScanRecord | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [activeTab, setActiveTab] = useState<'immediate' | 'treatment' | 'prevention' | 'monitoring'>('immediate');

  useEffect(() => {
    async function fetchScan() {
      if (!id) return;
      try {
        const data = await diseaseService.getScanById(parseInt(id, 10));
        setScan(data);
      } catch (err) {
        console.error('Failed to load scan:', err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchScan();
  }, [id]);

  const handleSaveTreatmentPlan = async () => {
    if (!scan) return;
    setIsSaving(true);
    await diseaseService.saveTreatment({
      scan_id: scan.id,
      immediate_action: scan.treatment ? scan.treatment[0] : 'Isolate and monitor affected leaves.',
      treatment_plan: scan.treatment || [],
      prevention: scan.prevention || [],
      monitoring: scan.monitoring || 'Inspect plot every 3 days.',
      expert_warning: scan.expert_warning
    });
    setIsSaving(false);
    setIsSaved(true);
    showToast(t('results.savedSuccess'), 'success');
  };

  if (isLoading) {
    return (
      <div className="py-24 text-center space-y-4">
        <div className="w-12 h-12 rounded-full border-4 border-agri-600 border-t-transparent animate-spin mx-auto" />
        <p className="text-sm font-medium text-stone-500">Loading diagnostic report...</p>
      </div>
    );
  }

  if (!scan) {
    return (
      <div className="bg-white dark:bg-darkbg-card rounded-3xl p-12 text-center max-w-lg mx-auto space-y-4 border border-stone-200 dark:border-darkbg-border">
        <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto" />
        <h3 className="text-lg font-bold text-stone-900 dark:text-stone-100">Scan Report Not Found</h3>
        <p className="text-xs text-stone-500">The requested disease report is unavailable or expired.</p>
        <Button onClick={() => navigate('/detect')}>Scan New Crop</Button>
      </div>
    );
  }

  const severityStyle = getSeverityStyles(scan.severity);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Top Breadcrumb & Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link
          to="/detect"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-stone-500 hover:text-stone-800 dark:hover:text-stone-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          {t('results.backToDetect')}
        </Link>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/history')}
          >
            {t('results.viewHistory')}
          </Button>

          <Button
            size="sm"
            onClick={handleSaveTreatmentPlan}
            disabled={isSaved}
            isLoading={isSaving}
            icon={isSaved ? <CheckCircle2 className="w-4 h-4" /> : <BookmarkCheck className="w-4 h-4" />}
            className={isSaved ? 'bg-emerald-700 hover:bg-emerald-700' : ''}
          >
            {isSaved ? 'Treatment Plan Saved' : t('results.savePlan')}
          </Button>
        </div>
      </div>

      {/* Main Diagnosis Highlight Card */}
      <div className="bg-white dark:bg-darkbg-card border border-stone-200 dark:border-darkbg-border rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left: Crop Photo */}
          <div className="lg:col-span-5 relative rounded-2xl overflow-hidden bg-stone-950 shadow-md">
            <img
              src={scan.image_url}
              alt={scan.disease}
              className="w-full aspect-4/3 object-cover"
            />
            <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-md text-white px-2.5 py-1 rounded-lg text-xs font-mono">
              ID: CS-{scan.id}
            </div>
            <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-[11px] text-stone-200 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-xl">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                {formatDate(scan.created_at)}
              </span>
              <span>Crop: {scan.crop}</span>
            </div>
          </div>

          {/* Right: Diagnosis Title & Primary Metrics */}
          <div className="lg:col-span-7 space-y-5">
            <div className="space-y-1">
              <span className="text-xs font-bold text-stone-400 uppercase tracking-wider">
                {scan.crop} Leaf Diagnosis
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 dark:text-stone-100 tracking-tight flex items-center gap-2">
                {scan.crop} {scan.disease}
              </h1>
              {scan.pathogen && scan.pathogen !== 'None' && (
                <p className="text-xs text-stone-500 dark:text-stone-400 italic">
                  Pathogen: {scan.pathogen}
                </p>
              )}
            </div>

            {/* Meters: Confidence & Severity */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <ConfidenceMeter confidence={scan.confidence} />
              <SeverityIndicator severity={scan.severity} />
            </div>

            {/* Expert Warning Banner if severe/moderate */}
            {scan.severity !== 'Healthy' && (
              <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/80 rounded-2xl p-4 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  <span className="font-bold">Agronomist Advisory: </span>
                  {scan.expert_warning || t('results.expertWarning')}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Disease Information Grid: Symptoms & Causes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Symptoms */}
        <div className="bg-white dark:bg-darkbg-card border border-stone-200 dark:border-darkbg-border rounded-3xl p-6 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-stone-900 dark:text-stone-100 font-bold text-base">
            <Activity className="w-5 h-5 text-agri-600" />
            <h3>{t('results.symptoms')}</h3>
          </div>
          <ul className="space-y-2 text-xs sm:text-sm text-stone-600 dark:text-stone-300">
            {scan.symptoms && scan.symptoms.map((sym, idx) => (
              <li key={idx} className="flex items-start gap-2.5">
                <span className="w-1.5 h-1.5 rounded-full bg-agri-500 shrink-0 mt-2" />
                <span className="leading-relaxed">{sym}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Causes */}
        <div className="bg-white dark:bg-darkbg-card border border-stone-200 dark:border-darkbg-border rounded-3xl p-6 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-stone-900 dark:text-stone-100 font-bold text-base">
            <ShieldAlert className="w-5 h-5 text-amber-500" />
            <h3>{t('results.causes')}</h3>
          </div>
          <ul className="space-y-2 text-xs sm:text-sm text-stone-600 dark:text-stone-300">
            {scan.causes && scan.causes.map((cause, idx) => (
              <li key={idx} className="flex items-start gap-2.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0 mt-2" />
                <span className="leading-relaxed">{cause}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Recommended Action Plan (Personalized Treatment) */}
      <div className="bg-white dark:bg-darkbg-card border border-stone-200 dark:border-darkbg-border rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-100 dark:border-darkbg-border pb-4">
          <div>
            <h2 className="text-xl font-bold text-stone-900 dark:text-stone-100">
              {t('results.actionPlan')}
            </h2>
            <p className="text-xs text-stone-500 dark:text-stone-400">
              Tailored agronomic recommendations formulated for your field conditions
            </p>
          </div>

          {/* Action Tabs */}
          <div className="flex flex-wrap gap-2">
            {[
              { key: 'immediate', label: t('results.immediateAction') },
              { key: 'treatment', label: t('results.treatment') },
              { key: 'prevention', label: t('results.prevention') },
              { key: 'monitoring', label: t('results.monitoring') }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
                  activeTab === tab.key
                    ? 'bg-agri-600 text-white shadow-xs'
                    : 'bg-stone-100 dark:bg-darkbg-border text-stone-600 dark:text-stone-300 hover:bg-stone-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content Display */}
        <div className="text-xs sm:text-sm text-stone-700 dark:text-stone-200 leading-relaxed min-h-[120px]">
          {activeTab === 'immediate' && (
            <div className="space-y-3 bg-emerald-50/50 dark:bg-emerald-950/20 p-5 rounded-2xl border border-emerald-200/60 dark:border-emerald-900/40">
              <span className="font-bold text-emerald-800 dark:text-emerald-300 block text-sm">
                Immediate Field Action:
              </span>
              <p className="leading-relaxed">
                {scan.treatment && scan.treatment[0]}
              </p>
              <p className="text-xs text-stone-500 dark:text-stone-400 italic">
                *Sanitize shears and wash hands thoroughly after handling diseased foliage.
              </p>
            </div>
          )}

          {activeTab === 'treatment' && (
            <ul className="space-y-3">
              {scan.treatment && scan.treatment.slice(1).map((item, idx) => (
                <li key={idx} className="flex items-start gap-3 bg-stone-50 dark:bg-darkbg-input p-3.5 rounded-xl border border-stone-200 dark:border-darkbg-border">
                  <CheckCircle2 className="w-4 h-4 text-agri-600 shrink-0 mt-0.5" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          )}

          {activeTab === 'prevention' && (
            <ul className="space-y-3">
              {scan.prevention && scan.prevention.map((item, idx) => (
                <li key={idx} className="flex items-start gap-3 bg-stone-50 dark:bg-darkbg-input p-3.5 rounded-xl border border-stone-200 dark:border-darkbg-border">
                  <Leaf className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          )}

          {activeTab === 'monitoring' && (
            <div className="bg-stone-50 dark:bg-darkbg-input p-5 rounded-2xl border border-stone-200 dark:border-darkbg-border space-y-2">
              <span className="font-bold text-stone-900 dark:text-stone-100 block text-sm">
                Follow-up & Recovery Monitoring:
              </span>
              <p>{scan.monitoring || 'Inspect plot leaves every 3 days. Re-scan on AgriSense after 5 days to verify disease containment.'}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
