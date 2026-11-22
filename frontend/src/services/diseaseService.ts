import { ScanRecord, TreatmentPlan } from '../types';
import { apiRequest, LocalDB } from './api';

export const diseaseService = {
  async analyzeCropImage(formData: FormData): Promise<ScanRecord> {
    const response = await apiRequest<ScanRecord>(
      '/disease/analyze',
      {
        method: 'POST',
        body: formData
      }
    );

    if (
      response.success &&
      response.data &&
      response.data.id &&
      response.data.disease
    ) {
      const scan = response.data;

      const existing = LocalDB.getScans();

      const alreadyExists = existing.some(
        item => item.id === scan.id
      );

      if (!alreadyExists) {
        existing.unshift(scan);
        LocalDB.saveScans(existing);
      }

      return scan;
    }

    throw new Error(
      response.message ||
      'Unable to analyze the uploaded image.'
    );
  },

  async getHistory(): Promise<ScanRecord[]> {
    try {
      const res = await apiRequest<ScanRecord[]>(
        '/disease/history'
      );

      if (res.success && Array.isArray(res.data)) {
        return res.data;
      }
    } catch (e) {
      console.error('History error:', e);
    }

    return LocalDB.getScans();
  },

  async getScanById(id: number): Promise<ScanRecord> {
    try {
      const res = await apiRequest<ScanRecord>(
        `/disease/${id}`
      );

      if (
        res.success &&
        res.data &&
        res.data.id
      ) {
        return res.data;
      }
    } catch (e) {
      console.error('Scan fetch error:', e);
    }

    const scans = LocalDB.getScans();

    const found = scans.find(
      scan => scan.id === id
    );

    if (!found) {
      throw new Error('Scan record not found.');
    }

    return found;
  },

  async saveTreatment(
    plan: Partial<TreatmentPlan>
  ): Promise<boolean> {
    try {
      const response = await apiRequest(
        '/treatments',
        {
          method: 'POST',
          body: JSON.stringify(plan)
        }
      );

      return response.success;
    } catch (e) {
      console.error('Treatment save error:', e);
      return false;
    }
  },

  async deleteScan(id: number): Promise<boolean> {
    try {
      await apiRequest(
        `/disease/${id}`,
        {
          method: 'DELETE'
        }
      );
    } catch (e) {
      console.error('Delete API error:', e);
    }

    const scans = LocalDB
      .getScans()
      .filter(scan => scan.id !== id);

    LocalDB.saveScans(scans);

    return true;
  }
};