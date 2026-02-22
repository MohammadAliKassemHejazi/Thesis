const axios = require('axios');

const TRANSLATION_SERVICE_URL = process.env.TRANSLATION_SERVICE_URL || 'http://translation-service:3001';

/**
 * Request translation from Translation Microservice
 */
async function requestTranslation(productId, name, description, targetLanguages) {
  try {
    const response = await axios.post(
      `${TRANSLATION_SERVICE_URL}/translate`,
      {
        original_request_id: productId,
        name: name,
        description: description,
        target_languages: targetLanguages,
      },
      {
        timeout: 30000, // 30 seconds
      }
    );
    return response.data;
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

/**
 * Delete all translations for a product
 */
async function deleteTranslations(productId) {
  try {
    const response = await axios.delete(
      `${TRANSLATION_SERVICE_URL}/translations/product/${productId}`,
      {
        timeout: 10000, // 10 seconds
      }
    );
    return response.data;
  } catch (error) {
    console.error(`❌ Failed to delete translations for product ${productId}:`, error.message);
    throw error; // Re-throw to allow caller to handle failure
  }
}

module.exports = {
  requestTranslation,
  getTranslation,
  deleteTranslations,
};
