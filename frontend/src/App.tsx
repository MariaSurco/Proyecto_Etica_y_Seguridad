import { BrowserRouter, Route, Routes } from "react-router-dom"
import { Toaster } from "sonner"

import { AppShell } from "@/components/layout/AppShell"
import { Explorar } from "@/pages/Explorar"
import { Queries } from "@/pages/Queries"
import { Modelo } from "@/pages/Modelo"
import { TradeOff } from "@/pages/TradeOff"
import { Etica } from "@/pages/Etica"
import { Usuarios } from "@/pages/Usuarios"
import { BankingApp } from "@/BankingApp"

function App() {
  return (
    <BrowserRouter>
      <Toaster richColors position="top-right" closeButton />
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Explorar />} />
          <Route path="queries" element={<Queries />} />
          <Route path="modelo" element={<Modelo />} />
          <Route path="trade-off" element={<TradeOff />} />
          <Route path="etica" element={<Etica />} />
          <Route path="usuarios" element={<Usuarios />} />
        </Route>
        <Route path="/banca/*" element={<BankingApp />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
