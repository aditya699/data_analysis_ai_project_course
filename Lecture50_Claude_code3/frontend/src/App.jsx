import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import Hero from './components/hero/Hero'
import UploadPanel from './components/upload/UploadPanel'
import FeatureGrid from './components/features/FeatureGrid'

// App only composes page sections. Logic lives in hooks/ and utils/.
export default function App() {
  return (
    <>
      <Header />
      <main className="container">
        <Hero />
        <UploadPanel />
        <FeatureGrid />
      </main>
      <Footer />
    </>
  )
}
