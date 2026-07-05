import React from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Float } from '@react-three/drei';
import { BookOpen, Sparkles, PlayCircle, Trophy, Rocket, BrainCircuit } from 'lucide-react';
import './styles.css';

const manifest = {
  "title": "Test",
  "topic": "AI",
  "audience": "beginners",
  "difficulty": "beginner",
  "learning_objectives": [
    "Learn"
  ],
  "modules": []
};

function FloatingOrb() {
  const meshRef = React.useRef(null);
  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.4;
      meshRef.current.rotation.y += delta * 0.5;
    }
  });

  return (
    <Float speed={2.2} rotationIntensity={1.2} floatIntensity={1.6}>
      <mesh ref={meshRef} position={[0, 0.3, 0]}>
        <torusKnotGeometry args={[0.7, 0.2, 180, 18]} />
        <meshStandardMaterial color="#7c3aed" emissive="#312e81" roughness={0.2} metalness={0.7} />
      </mesh>
    </Float>
  );
}

function App() {
  const moduleCount = manifest.modules?.length || 0;
  const totalMinutes = (manifest.modules || []).reduce((sum, module) => sum + (module.duration_minutes || 0), 0);

  return (
    <div className="course-shell">
      <header className="hero-card">
        <div className="hero-copy">
          <div className="badge-row">
            <span className="pill">✨ Interactive learning</span>
            <span className="pill">🎯 Khan-style mastery path</span>
          </div>
          <h1>{manifest.title || 'Course Experience'}</h1>
          <p>{manifest.topic || 'A polished learning journey with visuals, practice and progress.'}</p>
          <div className="hero-actions">
            <a className="primary-btn" href="#modules">Start learning</a>
            <span className="secondary-pill"><Sparkles size={16} /> Rich multimedia ready</span>
          </div>
          <div className="stats-grid">
            <div className="stat-card">
              <BookOpen size={18} />
              <div>
                <strong>{moduleCount}</strong>
                <span>Modules</span>
              </div>
            </div>
            <div className="stat-card">
              <Trophy size={18} />
              <div>
                <strong>{Math.ceil(totalMinutes / 60)}h</strong>
                <span>Estimated time</span>
              </div>
            </div>
          </div>
        </div>
        <div className="hero-visual">
          <Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
            <ambientLight intensity={0.8} />
            <directionalLight position={[2, 3, 3]} intensity={1.2} />
            <FloatingOrb />
            <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={1.2} />
          </Canvas>
        </div>
      </header>

      <section className="content-grid">
        <article className="panel">
          <div className="panel-title">
            <BrainCircuit size={20} />
            <h2>What you will learn</h2>
          </div>
          <ul>
            {(manifest.learning_objectives || []).map((objective, index) => (
              <li key={index}>🎯 {objective}</li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <div className="panel-title">
            <Rocket size={20} />
            <h2>Course highlights</h2>
          </div>
          <div className="chip-stack">
            <span className="chip">📚 Guided lessons</span>
            <span className="chip">🎮 Interactive quizzes</span>
            <span className="chip">🧠 3D visual aids</span>
            <span className="chip">✨ Emoji-rich UI</span>
          </div>
        </article>
      </section>

      <section id="modules" className="modules-section">
        <div className="panel-title">
          <PlayCircle size={20} />
          <h2>Modules</h2>
        </div>
        <div className="module-list">
          {(manifest.modules || []).map((module, index) => (
            <div className="module-card" key={module.slug || index}>
              <div className="module-head">
                <span className="module-index">0{index + 1}</span>
                <span className="module-status">{module.status || 'ready'}</span>
              </div>
              <h3>{module.title}</h3>
              <p>{module.description || 'A structured lesson designed for mastery.'}</p>
              <div className="module-meta">
                <span>🕒 {module.duration_minutes || 45} min</span>
                <span>📁 {module.files?.join(', ') || 'lesson_plan.json, script.md'}</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;
