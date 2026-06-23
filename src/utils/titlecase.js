export const toTitleCase = (str) => {
  if (!str) return '';
  
  // Pass 1: Standard Title Case (e.g., "ETHICS-II" -> "Ethics-Ii")
  let titleCased = str.toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
  
  const romanRegex = /\b(I|Ii|Iii|Iv|V|Vi|Vii|Viii|Ix|X)\b/g;
  
  return titleCased.replace(romanRegex, (match) => match.toUpperCase());
};