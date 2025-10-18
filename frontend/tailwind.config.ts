import type { Config } from "tailwindcss"

/**
 * Design System Configuration for SaaS Medical Tracker
 * 
 * This configuration extends Tailwind CSS with application-specific design tokens:
 * - Medical-themed color palette optimized for accessibility
 * - Healthcare-appropriate spacing and typography scales
 * - Custom components and utility classes
 * - Responsive breakpoints for mobile-first medical forms
 */
const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      // Medical-themed color palette with accessibility considerations
      colors: {
        // Base system colors (shadcn/ui compatibility)
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        
        // Primary brand colors (medical blue/teal palette)
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
          50: "#f0f9ff",
          100: "#e0f2fe", 
          200: "#bae6fd",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#0ea5e9", // Primary brand color
          600: "#0284c7",
          700: "#0369a1",
          800: "#075985",
          900: "#0c4a6e",
        },
        
        // Secondary colors (warm gray for balance)
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
          50: "#f9fafb",
          100: "#f3f4f6",
          200: "#e5e7eb",
          300: "#d1d5db",
          400: "#9ca3af",
          500: "#6b7280",
          600: "#4b5563",
          700: "#374151",
          800: "#1f2937",
          900: "#111827",
        },

        // Medical status colors
        medical: {
          // Health status indicators
          excellent: "#10b981", // Green - feeling great
          good: "#059669",      // Green-600 
          fair: "#f59e0b",      // Amber - okay/warning
          poor: "#f97316",      // Orange - not great  
          critical: "#ef4444",  // Red - urgent/bad
          
          // Medication adherence
          taken: "#10b981",     // Green - medication taken
          missed: "#f97316",    // Orange - missed dose
          late: "#f59e0b",      // Amber - taken late
          
          // Symptom severity
          mild: "#10b981",      // Green - mild symptoms
          moderate: "#f59e0b",  // Amber - moderate
          severe: "#f97316",    // Orange - severe
          emergency: "#ef4444", // Red - emergency
        },

        // Semantic colors
        success: {
          DEFAULT: "#10b981",
          light: "#d1fae5",
          dark: "#059669",
        },
        warning: {
          DEFAULT: "#f59e0b", 
          light: "#fef3c7",
          dark: "#d97706",
        },
        error: {
          DEFAULT: "#ef4444",
          light: "#fee2e2", 
          dark: "#dc2626",
        },
        info: {
          DEFAULT: "#3b82f6",
          light: "#dbeafe",
          dark: "#1d4ed8", 
        },

        // Standard shadcn colors
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },

      // Enhanced typography scale for medical forms and data
      fontSize: {
        // Accessible font sizes for medical information
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }], 
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        
        // Medical-specific text sizes
        'medical-label': ['0.875rem', { lineHeight: '1.25rem', fontWeight: '500' }],
        'medical-value': ['1rem', { lineHeight: '1.5rem', fontWeight: '600' }],
        'medical-caption': ['0.75rem', { lineHeight: '1rem', fontWeight: '400' }],
        'status-badge': ['0.75rem', { lineHeight: '1rem', fontWeight: '600' }],
      },

      // Medical form specific spacing
      spacing: {
        '18': '4.5rem',   // 72px - form section spacing
        '22': '5.5rem',   // 88px - card spacing
        '88': '22rem',    // 352px - sidebar width
        '128': '32rem',   // 512px - form max width
        
        // Form-specific spacing
        'form-gap': '1.5rem',        // 24px - between form sections
        'field-gap': '1rem',         // 16px - between form fields
        'label-gap': '0.5rem',       // 8px - label to input gap
        'button-gap': '0.75rem',     // 12px - between buttons
      },
      // Enhanced border radius scale for medical UI
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        
        // Medical component specific radius
        'card': '0.75rem',        // 12px - medical cards
        'form': '0.5rem',         // 8px - form fields  
        'badge': '0.375rem',      // 6px - status badges
        'button': '0.5rem',       // 8px - buttons
      },

      // Medical-themed animations and transitions
      keyframes: {
        // Existing shadcn animations
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        
        // Medical status animations
        "pulse-health": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        "slide-status": {
          from: { transform: "translateX(-100%)" },
          to: { transform: "translateX(0)" },
        },
        "fade-in-up": {
          from: { 
            opacity: "0",
            transform: "translateY(10px)"
          },
          to: { 
            opacity: "1",
            transform: "translateY(0)"
          },
        },
        "loading-dots": {
          "0%, 80%, 100%": { transform: "scale(0)" },
          "40%": { transform: "scale(1)" },
        },
      },
      
      animation: {
        // Existing animations
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        
        // Medical UI animations
        "pulse-health": "pulse-health 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-status": "slide-status 0.3s ease-out",
        "fade-in-up": "fade-in-up 0.3s ease-out",
        "loading-dots": "loading-dots 1.4s ease-in-out infinite both",
      },

      // Custom shadows for medical components
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'card-hover': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'form': '0 0 0 1px rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'status': '0 0 0 1px rgba(0, 0, 0, 0.1), 0 1px 3px 0 rgba(0, 0, 0, 0.1)',
      },

      // Medical component specific breakpoints
      screens: {
        'mobile': '390px',   // Mobile form optimization
        'tablet': '768px',   // Tablet layout
        'desktop': '1024px', // Desktop layout
        'wide': '1440px',    // Wide screen layout
      },
    },
  },
  plugins: [
    // @ts-ignore - tailwindcss-animate plugin
    require("tailwindcss-animate"),
  ],
}

export default config