import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ChakraProvider, createSystem, defaultConfig } from '@chakra-ui/react'
import theme from './theme'
import './index.css'
import App from './App'

// Create a proper system for Chakra UI v3
const system = createSystem(defaultConfig, { theme })

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ChakraProvider value={system}>
        <App />
      </ChakraProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
