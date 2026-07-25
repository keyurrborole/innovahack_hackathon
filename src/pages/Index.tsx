
import { useEffect } from 'react';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import Features from '../components/Features';
import HowItWorks from '../components/HowItWorks';
import Testimonials from '../components/Testimonials';
import Pricing from '../components/Pricing';
import FAQ from '../components/FAQ';
import CTA from '../components/CTA';
import Footer from '../components/Footer';
import ScrollToTop from '../components/ScrollToTop';
import ChatBot from '../components/ChatBot';
import ThreeBackground from '../components/ThreeBackground';
import useScrollAnimation from '../utils/useScrollAnimation';

const Index = () => {
  // Initialize scroll animations
  useScrollAnimation();

  // Set page title
  useEffect(() => {
    document.title = "FundFlow Trace | Internal fund flow tracking for fraud detection (PS3)";
  }, []);
  
  return (
    <div className="min-h-screen overflow-x-hidden bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-crypto-blue dark:via-[#0d1117] dark:to-crypto-blue transition-colors duration-300">
      <ThreeBackground variant="particles" />
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <Testimonials />
      <Pricing />
      <FAQ />
      <CTA />
      <Footer />
      <ScrollToTop />
      <ChatBot />
    </div>
  );
};

export default Index;
