const Product = require('../models/Product');
const { requestTranslation, getTranslation, deleteTranslations } = require('../services/translationService');

exports.createProduct = async (req, res) => {
  const {
    name,
    description,
    price = null,
    auto_translate = true,
    target_languages = ['es', 'fr', 'de'],
  } = req.body;

  if (!name) {
    return res.status(400).json({ error: 'Product name is required' });
  }

  if (!description) {
    return res.status(400).json({ error: 'Product description is required' });
  }

  try {
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

    res.status(201).json({
      id: product.id,
      name: product.name,
      description: product.description,
      price: product.price ? parseFloat(product.price) : null,
      lang: 'en',
    });
  } catch (error) {
    console.error('❌ Error creating product:', error);
    res.status(500).json({ error: 'Failed to create product' });
  }
};

exports.getProduct = async (req, res) => {
  const productId = parseInt(req.params.id);
  const lang = req.query.lang || 'en';

  if (isNaN(productId)) {
    return res.status(400).json({ error: 'Invalid product ID' });
  }

  try {
    // Get product from database
    const product = await Product.findByPk(productId);

    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }

    // If English or no language specified, return original
    if (lang === 'en') {
      return res.json({
        id: product.id,
        name: product.name,
        description: product.description,
        price: product.price ? parseFloat(product.price) : null,
        lang: 'en',
      });
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

      return res.json({
        id: product.id,
        name: translatedName,
        description: translatedDescription,
        price: product.price ? parseFloat(product.price) : null,
        lang: lang,
      });
    } else {
      // Fallback to English if translation not found
      console.warn(`⚠️  Translation not found for product ${productId} in ${lang}, falling back to English`);
      return res.json({
        id: product.id,
        name: product.name,
        description: product.description,
        price: product.price ? parseFloat(product.price) : null,
        lang: 'en',
      });
    }
  } catch (error) {
    console.error('❌ Error fetching product:', error);
    res.status(500).json({ error: 'Failed to fetch product' });
  }
};

exports.listProducts = async (req, res) => {
  const skip = parseInt(req.query.skip) || 0;
  const limit = parseInt(req.query.limit) || 100;
  const lang = req.query.lang || 'en';

  try {
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

    res.json(responseProducts);
  } catch (error) {
    console.error('❌ Error listing products:', error);
    res.status(500).json({ error: 'Failed to list products' });
  }
};

exports.updateProduct = async (req, res) => {
  const productId = parseInt(req.params.id);
  const {
    name,
    description,
    price = null,
    auto_translate = true,
    target_languages = ['es', 'fr', 'de'],
  } = req.body;

  if (isNaN(productId)) {
    return res.status(400).json({ error: 'Invalid product ID' });
  }

  if (!name) {
    return res.status(400).json({ error: 'Product name is required' });
  }

  if (!description) {
    return res.status(400).json({ error: 'Product description is required' });
  }

  try {
    // Update product in database
    const [affectedCount, affectedRows] = await Product.update(
      { name, description, price, updated_at: new Date() },
      { where: { id: productId }, returning: true }
    );

    if (affectedCount === 0) {
      return res.status(404).json({ error: 'Product not found' });
    }

    const product = affectedRows[0];
    console.log(`✅ Updated product: ${product.id} - ${product.name}`);

    // Request new translations if enabled
    if (auto_translate && target_languages.length > 0) {
      console.log(`🌐 Requesting translations for updated product ${product.id}`);

      requestTranslation(product.id, name, description, target_languages)
        .catch(err => console.error('Translation request error:', err));
    }

    res.json({
      id: product.id,
      name: product.name,
      description: product.description,
      price: product.price ? parseFloat(product.price) : null,
      lang: 'en',
    });
  } catch (error) {
    console.error('❌ Error updating product:', error);
    res.status(500).json({ error: 'Failed to update product' });
  }
};

exports.deleteProduct = async (req, res) => {
  const productId = parseInt(req.params.id);

  if (isNaN(productId)) {
    return res.status(400).json({ error: 'Invalid product ID' });
  }

  try {
    // Check if product exists first
    const product = await Product.findByPk(productId);
    if (!product) {
      return res.status(404).json({ error: 'Product not found' });
    }

    // Attempt to delete translations first
    try {
      console.log(`🗑️  Deleting translations for product ${productId}...`);
      await deleteTranslations(productId);
      console.log(`✅ Translations deleted for product ${productId}`);
    } catch (translationError) {
      console.error(`❌ Aborting product deletion. Failed to delete translations:`, translationError.message);
      return res.status(500).json({
        error: 'Failed to delete associated translations. Product deletion aborted.'
      });
    }

    // Delete product from database
    const deletedCount = await Product.destroy({ where: { id: productId } });

    if (deletedCount === 0) {
      return res.status(404).json({ error: 'Product not found' });
    }

    console.log(`✅ Deleted product: ${productId}`);
    res.json({ message: `Product ${productId} deleted successfully` });
  } catch (error) {
    console.error('❌ Error deleting product:', error);
    res.status(500).json({ error: 'Failed to delete product' });
  }
};
