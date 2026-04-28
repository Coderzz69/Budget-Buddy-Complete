export type IconSymbolName = 
  | 'dollarsign.circle.fill'
  | 'cart.fill'
  | 'car.fill'
  | 'gamecontroller.fill'
  | 'bolt.fill'
  | 'heart.fill'
  | 'book.fill'
  | 'chart.pie.fill'
  | 'creditcard'
  | 'pencil'
  | 'trash'
  | 'magnifyingglass'
  | 'person.circle'
  | 'plus'
  | 'arrow.down'
  | 'arrow.up'
  | 'list.bullet.rectangle.fill'
  | 'bag.fill'
  | 'ellipsis.circle.fill'
  | 'fork.knife'
  | 'airplane'
  | 'doc.text.fill'
  | 'play.circle.fill'
  | 'shippingbox.fill'
  | 'play.tv.fill'
  | 'cup.and.saucer.fill'
  | 'applelogo'
  | 'creditcard.fill'
  | 'shield.fill'
  | 'cart.badge.plus'
  | 'graduationcap.fill'
  | 'leaf.fill'
  | 'wineglass.fill'
  | 'fitness';

export const getTransactionIcon = (categoryName?: string, note?: string): IconSymbolName => {
  const name = categoryName?.toLowerCase() || '';
  const noteLower = note?.toLowerCase() || '';

  // Priority 1: Category Name Mapping
  if (name.includes('food') || name.includes('dining') || name.includes('restaurant')) return 'fork.knife';
  if (name.includes('shop') || name.includes('market') || name.includes('grocery')) return 'bag.fill';
  if (name.includes('transport') || name.includes('taxi') || name.includes('uber')) return 'car.fill';
  if (name.includes('travel') || name.includes('flight') || name.includes('hotel')) return 'airplane';
  if (name.includes('health') || name.includes('medical') || name.includes('pharmacy')) return 'heart.fill';
  if (name.includes('bill') || name.includes('utility') || name.includes('rent') || name.includes('recharge')) return 'doc.text.fill';
  if (name.includes('entertainment') || name.includes('movie') || name.includes('game')) return 'play.circle.fill';
  if (name.includes('education') || name.includes('book') || name.includes('course')) return 'graduationcap.fill';
  if (name.includes('income') || name.includes('salary') || name.includes('bonus')) return 'dollarsign.circle.fill';
  if (name.includes('investment') || name.includes('stock')) return 'chart.pie.fill';
  if (name.includes('alcohol') || name.includes('drink') || name.includes('bar')) return 'wineglass.fill';
  if (name.includes('fitness') || name.includes('gym')) return 'fitness';
  if (name.includes('insurance') || name.includes('secure')) return 'shield.fill';

  // Priority 2: Keyword detection in notes
  if (noteLower.includes('amazon') || noteLower.includes('flipkart')) return 'shippingbox.fill';
  if (noteLower.includes('netflix') || noteLower.includes('spotify') || noteLower.includes('youtube')) return 'play.tv.fill';
  if (noteLower.includes('starbucks') || noteLower.includes('coffee') || noteLower.includes('chai')) return 'cup.and.saucer.fill';
  if (noteLower.includes('apple') || noteLower.includes('icloud')) return 'applelogo';
  if (noteLower.includes('zomato') || noteLower.includes('swiggy')) return 'fork.knife';
  if (noteLower.includes('uber') || noteLower.includes('ola')) return 'car.fill';
  
  return 'creditcard.fill'; // Standard premium fallback instead of dots
};
