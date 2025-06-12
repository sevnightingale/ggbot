export default function Home() {
  return (
    <div style={{ 
      padding: '2rem', 
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f0f0f0',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        textAlign: 'center'
      }}>
        <h1 style={{ color: '#333', marginBottom: '1rem' }}>🤖 GGBot Test Page</h1>
        <p style={{ color: '#666', marginBottom: '1rem' }}>
          If you can see this, Vercel deployment is working!
        </p>
        <div style={{ 
          backgroundColor: '#e8f5e8', 
          padding: '1rem', 
          borderRadius: '4px',
          border: '1px solid #4caf50'
        }}>
          <strong style={{ color: '#2e7d32' }}>✅ SUCCESS:</strong>
          <br />
          Next.js is rendering correctly on Vercel
        </div>
        <p style={{ color: '#999', fontSize: '0.9rem', marginTop: '1rem' }}>
          Time: {new Date().toLocaleString()}
        </p>
      </div>
    </div>
  )
}