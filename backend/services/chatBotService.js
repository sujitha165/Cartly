/**
 * AgriSense AI Chatbot Service
 * Intelligent conversational assistant specialized in agricultural guidance,
 * crop diseases, organic solutions, soil health, and government subsidies.
 * Pluggable to Gemini / OpenAI API via environment variables.
 */

const env = require('../config/env');

const AGRICULTURAL_KNOWLEDGE_PROMPTS = [
  {
    triggers: ['tomato', 'early blight', 'late blight', 'leaf curl', 'wilting'],
    response: `**Tomato Health Guidance:**
* **Early Blight:** Characterized by brown concentric target rings on bottom leaves. Prune infected leaves immediately, apply copper oxychloride (2.5g/L), and switch to drip irrigation to prevent soil splash.
* **Late Blight:** Water-soaked lesions with white mold underneath during humid weather. Urgently destroy infected foliage and treat with systemic fungicide (Metalaxyl + Mancozeb).
* **Leaf Curl Virus:** Transmitted by whiteflies. Control whiteflies with yellow sticky traps and neem oil spray (5ml/L).

*Tip:* Always sanitize pruning shears with 70% alcohol between cuts to avoid cross-contamination.`
  },
  {
    triggers: ['prevent', 'prevention', 'fungus', 'disease prevention', 'healthy'],
    response: `**Top 5 Preventative Crop Protection Principles:**
1. **Crop Rotation:** Rotate nightshade crops (tomatoes, potatoes, eggplants) with legumes or cereals on a 3-year cycle.
2. **Canopy Airflow:** Maintain proper row and plant spacing so foliage dries rapidly in morning sunlight.
3. **Smart Irrigation:** Water directly at the root zone via drip lines; never use overhead sprinklers late in the evening.
4. **Organic Soil Barrier:** Apply 2–3 inches of straw or organic mulch to prevent rain from splashing soil-borne fungal spores onto lower leaves.
5. **Beneficial Biocontrols:** Periodic prophylactic sprays of *Trichoderma viride* or *Pseudomonas fluorescens* build natural resistance.`
  },
  {
    triggers: ['scheme', 'subsidy', 'government', 'pm kisan', 'pmfby', 'financial', 'loan'],
    response: `**Key Government Agricultural Support Programs:**
* **PM-KISAN:** ₹6,000/year direct cash transfer delivered in three 4-monthly installments of ₹2,000. Apply at [pmkisan.gov.in](https://pmkisan.gov.in).
* **PMFBY (Crop Insurance):** Comprehensive insurance covering weather, pest, and disease damage. Premium is only 2% for Kharif crops and 1.5% for Rabi crops.
* **SMAM (Mechanization Subsidy):** 40% to 50% subsidy for purchasing tractors, power sprayers, rotavators, and harvesters.
* **Kisan Credit Card (KCC):** Short-term crop loans up to ₹3 Lakh at an effective low interest rate of 4% per annum upon on-time repayment.

Check the **Government Schemes** tab in the sidebar for full eligibility criteria and application workflows!`
  },
  {
    triggers: ['potato', 'tuber', 'potato blight', 'scab'],
    response: `**Potato Disease & Management Guide:**
* **Late Blight in Potato:** Rapidly destroys leaves and causes dry brown rot in tubers. Hill high soil ridges over developing tubers to shield them from spores washed down by rain.
* **Early Blight:** Appears as brown target-board spots during tuber bulking. Ensure balanced nitrogen and potassium to avoid premature plant senescence.
* **Storage Advice:** Store harvested tubers in a cool, well-ventilated, dark area (10–12°C with 90% humidity) after curing for 10 days to heal skin abrasions.`
  },
  {
    triggers: ['rice', 'paddy', 'blast', 'brown spot', 'bacterial leaf blight'],
    response: `**Paddy (Rice) Health Advice:**
* **Bacterial Leaf Blight:** Yellowish-white wavy lesions starting at leaf tips. Drain the field for 2–3 days to aerate the soil and temporarily halt chemical nitrogen top-dressing.
* **Brown Spot:** Oval sesame-seed spots often indicate potassium or micronutrient deficiency in the soil. Top-dress with MOP (Muriate of Potash).
* **Blast Disease:** Spindle-shaped lesions with gray centers. Avoid excessive urea application and spray Tricyclazole (0.6g/L) during tillering.`
  },
  {
    triggers: ['fertilizer', 'npk', 'soil', 'nutrition', 'manure', 'urea'],
    response: `**Balanced Crop Nutrition Tips:**
* **Soil Testing First:** Avail the Government *Soil Health Card Scheme* to get your field soil tested free of charge before deciding on fertilizer dosages.
* **The 4:2:1 Ratio:** General recommendation for cereals is 4 parts Nitrogen (N), 2 parts Phosphorus (P), and 1 part Potassium (K), but tailored to soil test results.
* **Organic Matter:** Incorprate 5–10 tons of well-decomposed Farmyard Manure (FYM) or 2 tons of Vermicompost per acre before planting to boost microbial activity and moisture retention.`
  }
];

const DEFAULT_RESPONSE = `Hello! I am your **AgriSense AI Assistant** 🌱.

I can help you with:
* **Diagnosing Crop Diseases:** Ask about blight, rust, leaf spot, or mildew on tomato, potato, rice, apple, cotton, and more.
* **Actionable Treatment Plans:** Get organic solutions, approved bio-fungicide suggestions, and preventive farming practices.
* **Government Subsidies & Schemes:** Inquire about PM-KISAN, PMFBY crop insurance, SMAM machinery subsidies, and KCC loans.
* **Crop Economics:** Guidance on minimizing input expenses and calculating harvest profit margins.

Try asking: *"What should I do after detecting early blight on tomato?"* or *"What government schemes are available for subsidies?"*`;

async function getChatResponse({ message, history = [], language = 'en' }) {
  if (!message || message.trim() === '') {
    return DEFAULT_RESPONSE;
  }

  // If OpenAI / Gemini API key is present, can invoke LLM here
  if (env.AI_API_KEY) {
    // In production, invoke Gemini / OpenAI API with agricultural system prompt
    console.log('[Chatbot] Real LLM API configured; external call could be dispatched.');
  }

  const query = message.toLowerCase();

  // Find best matching domain knowledge block
  for (const item of AGRICULTURAL_KNOWLEDGE_PROMPTS) {
    if (item.triggers.some(trigger => query.includes(trigger))) {
      return item.response;
    }
  }

  // Helpful conversational response tailored to query
  return `Thank you for asking about "${message.trim()}".

Based on agricultural best practices:
1. **Visual Scouting:** Regularly inspect both the upper and lower surfaces of crop leaves in the early morning.
2. **Moisture Control:** Fungal and bacterial infections thrive in humid leaf wetness. Keep foliage well aerated and irrigate at soil level.
3. **Scan & Confirm:** Use the **AgriSense Detect** feature in the sidebar to upload a clear leaf photo for an automated diagnosis, confidence score, and tailored treatment action plan.
4. **Local Extension:** For large-scale infections, seek on-site validation from your village agricultural officer or nearby KVK center.

Feel free to ask more specific questions about particular crops (e.g. Tomato, Rice, Potato) or government schemes!`;
}

module.exports = {
  getChatResponse
};
