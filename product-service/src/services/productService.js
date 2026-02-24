const Product = require('../models/Product');
const { requestTranslation, getTranslation, deleteTranslations } = require('./translationService');

class ProductService {
  async createProduct(data) {
    const { name, description, price, auto_translate = true, target_languages = ['es', 'fr', 'de'] } = data;

    // Insert product into database
    const product = await Product.create({
      name,
      description,
      price
    });

    console.log(`✅ Created product: ${product.id} - ${product.name}`);

    // Request translations if enabled
    if (auto_translate && target_languages.length > 0) {
      console.log(`🌐 Requesting translations for product ${product.id}`);

      // Fire and forget - don't wait for translation to complete
      requestTranslation(product.id, name, description, target_languages)
        .catch(err => console.error('Translation request error:', err));
    }

    return {
      id: product.id,
      name: product.name,
      description: product.description,
      price: product.price ? parseFloat(product.price) : null,
      lang: 'en',
    };
  }

  async getProduct(id, lang = 'en') {
    const product = await Product.findByPk(id);

    if (!product) {
      return null;
    }

    if (lang === 'en') {
      return {
        id: product.id,
        name: product.name,
        description: product.description,
        price: product.price ? parseFloat(product.price) : null,
        lang: 'en',
      };
    }

    // Get translation
    const translation = await getTranslation(product.id, lang);

    if (translation) {
      const translatedName = (translation.is_edited && translation.edited_name)
        ? translation.edited_name
        : translation.translated_name;

      const translatedDescription = (translation.is_edited && translation.edited_description)
        ? translation.edited_description
        : translation.translated_description;

      return {
        id: product.id,
        name: translatedName,
        description: translatedDescription,
        price: product.price ? parseFloat(product.price) : null,
        lang: lang,
      };
    } else {
      console.warn(`⚠️  Translation not found for product ${id} in ${lang}, falling back to English`);
      return {
        id: product.id,
        name: product.name,
        description: product.description,
        price: product.price ? parseFloat(product.price) : null,
        lang: 'en',
      };
    }
  }

  async listProducts(skip = 0, limit = 100, lang = 'en') {
    const products = await Product.findAll({
      offset: skip,
      limit: limit,
      order: [['id', 'ASC']]
    });

    const responseProducts = [];

    for (const product of products) {
      if (lang === 'en') {
        responseProducts.push({
          id: product.id,
          name: product.name,
          description: product.description,
          price: product.price ? parseFloat(product.price) : null,
          lang: 'en',
        });
      } else {
        // Try to get translation
        const translation = await getTranslation(product.id, lang);
        if (translation) {
          const translatedName = (translation.is_edited && translation.edited_name)
            ? translation.edited_name
            : translation.translated_name;

          const translatedDescription = (translation.is_edited && translation.edited_description)
            ? translation.edited_description
            : translation.translated_description;

          responseProducts.push({
            id: product.id,
            name: translatedName,
            description: translatedDescription,
            price: product.price ? parseFloat(product.price) : null,
            lang: lang,
          });
        } else {
          // Fallback to English
          responseProducts.push({
            id: product.id,
            name: product.name,
            description: product.description,
            price: product.price ? parseFloat(product.price) : null,
            lang: 'en',
          });
        }
      }
    }
    return responseProducts;
  }

  async updateProduct(id, data) {
    const { name, description, price, auto_translate = true, target_languages = ['es', 'fr', 'de'] } = data;

    const [affectedCount, affectedRows] = await Product.update(
      { name, description, price, updated_at: new Date() },
      { where: { id: id }, returning: true }
    );

    if (affectedCount === 0) {
      return null;
    }

    const product = affectedRows[0];
    console.log(`✅ Updated product: ${product.id} - ${product.name}`);

    // Request new translations if enabled
    if (auto_translate && target_languages.length > 0) {
      console.log(`🌐 Requesting translations for updated product ${product.id}`);

      requestTranslation(product.id, name, description, target_languages)
        .catch(err => console.error('Translation request error:', err));
    }

    return {
      id: product.id,
      name: product.name,
      description: product.description,
      price: product.price ? parseFloat(product.price) : null,
      lang: 'en',
    };
  }

  async deleteProduct(id) {
    const product = await Product.findByPk(id);
    if (!product) {
      return null; // Not found
    }

    try {
      console.log(`🗑️  Deleting translations for product ${id}...`);
      await deleteTranslations(id);
      console.log(`✅ Translations deleted for product ${id}`);
    } catch (translationError) {
      console.error(`❌ Aborting product deletion. Failed to delete translations:`, translationError.message);
      throw new Error('Failed to delete associated translations. Product deletion aborted.');
    }

    const deletedCount = await Product.destroy({ where: { id: id } });
    return deletedCount > 0;
  }
}

module.exports = new ProductService();
