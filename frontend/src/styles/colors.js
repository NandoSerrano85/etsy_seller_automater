// Pastel Color Palette Configuration
export const pastelColors = {
  // Primary pastels
  lavender: {
    50: '#f8f7ff',
    100: '#f0edff',
    200: '#e2dcff',
    300: '#c9bbff',
    400: '#b19aff',
    500: '#9679ff',
    600: '#7c5ce8',
    700: '#6442c4',
    800: '#523b99',
    900: '#43357a',
  },

  mint: {
    50: '#f0fdf9',
    100: '#ccfdf0',
    200: '#99fae1',
    300: '#5eead4',
    400: '#2dd4bf',
    500: '#14b8a6',
    600: '#0d9488',
    700: '#0f766e',
    800: '#115e59',
    900: '#134e4a',
  },

  peach: {
    50: '#fff7ed',
    100: '#ffedd5',
    200: '#fed7aa',
    300: '#fdba74',
    400: '#fb923c',
    500: '#f97316',
    600: '#ea580c',
    700: '#c2410c',
    800: '#9a3412',
    900: '#7c2d12',
  },

  rose: {
    50: '#fff1f2',
    100: '#ffe4e6',
    200: '#fecdd3',
    300: '#fda4af',
    400: '#fb7185',
    500: '#f43f5e',
    600: '#e11d48',
    700: '#be123c',
    800: '#9f1239',
    900: '#881337',
  },

  sky: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
  },

  sage: {
    50: '#f6f7f6',
    100: '#e8f0e8',
    200: '#d1e0d1',
    300: '#a8c5a8',
    400: '#7ba67b',
    500: '#5d8a5d',
    600: '#4a6f4a',
    700: '#3d583d',
    800: '#344834',
    900: '#2d3c2d',
  },
};

// Semantic color mapping
export const semanticColors = {
  primary: pastelColors.lavender,
  secondary: pastelColors.mint,
  accent: pastelColors.peach,
  success: pastelColors.mint,
  warning: pastelColors.peach,
  error: pastelColors.rose,
  info: pastelColors.sky,
  neutral: pastelColors.sage,
};

// Component-specific color utilities
export const getComponentColors = (color = 'primary', variant = 'default') => {
  const colorPalette = semanticColors[color] || semanticColors.primary;

  const variants = {
    default: {
      bg: colorPalette[100],
      text: colorPalette[800],
      border: colorPalette[200],
      hover: colorPalette[200],
    },
    subtle: {
      bg: colorPalette[50],
      text: colorPalette[700],
      border: colorPalette[100],
      hover: colorPalette[100],
    },
    solid: {
      bg: colorPalette[500],
      text: 'white',
      border: colorPalette[500],
      hover: colorPalette[600],
    },
    outline: {
      bg: 'transparent',
      text: colorPalette[600],
      border: colorPalette[300],
      hover: colorPalette[50],
    },
  };

  return variants[variant] || variants.default;
};

export default pastelColors;
