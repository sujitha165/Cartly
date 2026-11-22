import { apiRequest } from './api';

export const chatService = {
  async sendMessage(message: string, language: string = 'en'): Promise<string> {
    try {
      const res = await apiRequest<{ reply: string }>('/chat', {
        method: 'POST',
        body: JSON.stringify({ message, language })
      });
      if (res.data && res.data.reply) {
        return res.data.reply;
      }
    } catch (e) {
      // ignore
    }

    // Local fallback replies
    const q = message.toLowerCase();
    if (q.includes('tomato') || q.includes('blight')) {
      return `**Tomato Health Guidance:**\n* **Early Blight:** Identified by concentric target rings on lower leaves. Prune infected foliage immediately, apply copper oxychloride (2.5g/L), and switch to drip irrigation to prevent soil splash.\n* **Late Blight:** Water-soaked lesions with white mold in humid conditions. Remove affected plants and treat with systemic fungicide.\n\n*Pro-tip:* Sanitize pruning shears with 70% alcohol between cuts.`;
    }
    if (q.includes('prevent') || q.includes('fungus')) {
      return `**Top Disease Prevention Principles:**\n1. **Crop Rotation:** Rotate with non-solanaceous crops on a 3-year cycle.\n2. **Air Circulation:** Maintain proper row spacing so foliage dries quickly in morning sun.\n3. **Soil Mulching:** Apply 2-3 inches of straw mulch to block soil-to-leaf splashing.\n4. **Bio-agents:** Spray *Trichoderma viride* preventively to build plant resistance.`;
    }
    if (q.includes('scheme') || q.includes('subsidy') || q.includes('loan')) {
      return `**Key Government Schemes Available:**\n* **PM-KISAN:** ₹6,000/year direct bank transfer in 3 installments of ₹2,000.\n* **PMFBY:** Crop insurance with premium rates as low as 1.5% - 2%.\n* **SMAM:** 40% - 50% subsidy for purchasing tractors, sprayers, and farm machinery.\n* **KCC:** Short-term credit limit up to ₹3 Lakh at 4% interest rate.\n\nVisit the **Govt Schemes** page in the sidebar for complete details!`;
    }

    return `Thank you for asking about "${message}".\n\nFor optimal crop vitality, maintain balanced soil nutrition, use drip irrigation at ground level, and regularly inspect lower leaf undersides in the morning.\n\nUse our **Detect Disease** feature to upload an image of any affected leaves for an instant AI scan!`;
  }
};
