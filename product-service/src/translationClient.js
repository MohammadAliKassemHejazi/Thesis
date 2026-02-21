const axios = require('axios');

const TRANSLATION_SERVICE_URL = process.env.TRANSLATION_SERVICE_URL || 'http://translation-service:3001';

/**
 * Request translation from Translation Microservice (Synchronous)
 * Returns array of translations after processing is complete.
 */
async function requestTranslation(productId, text, targetLanguages) {
  try {
    const response = await axios.post(
      `${TRANSLATION_SERVICE_URL}/translate`,
      {
        original_request_id: productId,
        text: text,
        target_languages: targetLanguages,
      },
      {
        timeout: 60000, // Increased to 60 seconds for synchronous processing
      }
    );
    console.log(`✅ Translation completed for product ${productId}: ${response.status} ${response.statusText}`);
    return response.data; // Returns array of translations
  } catch (error) {
    console.error('❌ Translation request failed:', error.message);
    return null;
  }
}

/**
 * Get translation for a product from Translation Microservice
 */
async function getTranslation(productId, language) {
  try {
    const response = await axios.get(
      `${TRANSLATION_SERVICE_URL}/translations/${productId}`,
      {
        params: { lang: language },
        timeout: 10000, // 10 seconds
      }
    );
    
    const translations = response.data;
    
    // Return the first matching translation
    if (translations && translations.length > 0) {
      return translations[0];
    }
    return null;
  } catch (error) {
    if (error.response && error.response.status === 404) {
      console.warn(`⚠️  Translation not found for product ${productId} in ${language}`);
    } else {
      console.error('❌ Failed to get translation:', error.message);
    }
    return null;
  }
}

module.exports = {
  requestTranslation,
  getTranslation,
};
