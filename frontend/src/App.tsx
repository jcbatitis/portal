import { createBrowserRouter, RouterProvider } from "react-router"
import { LoginPage } from "@/components/login-page"
import { HomePage, homeLoader } from "@/components/home-page"

const router = createBrowserRouter([
  {
    path: "/",
    element: <LoginPage />,
  },
  {
    path: "/home",
    element: <HomePage />,
    loader: homeLoader,
    errorElement: <LoginPage />,
    hydrateFallbackElement: null,
  },
])

function App() {
  return <RouterProvider router={router} />
}

export default App
