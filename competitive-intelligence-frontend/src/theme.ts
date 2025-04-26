import { extendTheme, type ThemeConfig } from "@chakra-ui/react";

const config: ThemeConfig = {
  initialColorMode: "dark",
  useSystemColorMode: false,
};

const theme = extendTheme({
  config,
  fonts: {
    heading: "'Inter', sans-serif",
    body: "'Inter', sans-serif",
  },
  colors: {
    brand: {
      50:  "#e3f9f8",
      500: "#00b5b5",
      700: "#008080",
    },
  },
});

export default theme;
