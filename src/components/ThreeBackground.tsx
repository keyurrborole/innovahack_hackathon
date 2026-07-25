import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface ThreeBackgroundProps {
  variant?: 'particles' | 'cubes' | 'waves';
}

const ThreeBackground = ({ variant = 'particles' }: ThreeBackgroundProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const animationIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.z = 30;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    rendererRef.current = renderer;
    containerRef.current.appendChild(renderer.domElement);

    // Create objects based on variant
    const objects: THREE.Object3D[] = [];

    if (variant === 'particles') {
      // Floating particles
      const particlesGeometry = new THREE.BufferGeometry();
      const particlesCount = 1000;
      const positions = new Float32Array(particlesCount * 3);
      const colors = new Float32Array(particlesCount * 3);

      for (let i = 0; i < particlesCount * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 100;
        positions[i + 1] = (Math.random() - 0.5) * 100;
        positions[i + 2] = (Math.random() - 0.5) * 100;

        // Purple and blue colors
        colors[i] = 0.5 + Math.random() * 0.5;
        colors[i + 1] = 0.2 + Math.random() * 0.3;
        colors[i + 2] = 0.8 + Math.random() * 0.2;
      }

      particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

      const particlesMaterial = new THREE.PointsMaterial({
        size: 0.5,
        vertexColors: true,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending
      });

      const particles = new THREE.Points(particlesGeometry, particlesMaterial);
      scene.add(particles);
      objects.push(particles);

    } else if (variant === 'cubes') {
      // Floating glowing cubes
      const cubeGeometry = new THREE.BoxGeometry(1, 1, 1);
      
      for (let i = 0; i < 30; i++) {
        const color = new THREE.Color().setHSL(Math.random() * 0.2 + 0.6, 0.8, 0.5);
        const material = new THREE.MeshPhongMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.5,
          transparent: true,
          opacity: 0.7
        });
        
        const cube = new THREE.Mesh(cubeGeometry, material);
        cube.position.set(
          (Math.random() - 0.5) * 50,
          (Math.random() - 0.5) * 50,
          (Math.random() - 0.5) * 50
        );
        cube.rotation.set(
          Math.random() * Math.PI,
          Math.random() * Math.PI,
          Math.random() * Math.PI
        );
        scene.add(cube);
        objects.push(cube);
      }

      // Add lights
      const ambientLight = new THREE.AmbientLight(0x404040);
      scene.add(ambientLight);
      
      const pointLight = new THREE.PointLight(0x8b5cf6, 1, 100);
      pointLight.position.set(0, 0, 20);
      scene.add(pointLight);

    } else if (variant === 'waves') {
      // Animated wave grid
      const geometry = new THREE.PlaneGeometry(50, 50, 30, 30);
      const material = new THREE.MeshPhongMaterial({
        color: 0x8b5cf6,
        emissive: 0x4c1d95,
        emissiveIntensity: 0.3,
        wireframe: true,
        transparent: true,
        opacity: 0.6
      });

      const plane = new THREE.Mesh(geometry, material);
      plane.rotation.x = -Math.PI / 4;
      scene.add(plane);
      objects.push(plane);

      // Lighting
      const ambientLight = new THREE.AmbientLight(0x404040);
      scene.add(ambientLight);
      
      const directionalLight = new THREE.DirectionalLight(0x8b5cf6, 1);
      directionalLight.position.set(0, 1, 1);
      scene.add(directionalLight);
    }

    // Animation
    let time = 0;
    const animate = () => {
      animationIdRef.current = requestAnimationFrame(animate);
      time += 0.01;

      if (variant === 'particles') {
        objects.forEach(obj => {
          obj.rotation.y += 0.001;
          obj.rotation.x += 0.0005;
        });
      } else if (variant === 'cubes') {
        objects.forEach((cube, i) => {
          cube.rotation.x += 0.01;
          cube.rotation.y += 0.01;
          cube.position.y += Math.sin(time + i) * 0.02;
        });
      } else if (variant === 'waves') {
        const plane = objects[0] as THREE.Mesh;
        const geometry = plane.geometry as THREE.PlaneGeometry;
        const positions = geometry.attributes.position.array as Float32Array;
        
        for (let i = 0; i < positions.length; i += 3) {
          const x = positions[i];
          const y = positions[i + 1];
          positions[i + 2] = Math.sin(x * 0.1 + time) * 2 + Math.cos(y * 0.1 + time) * 2;
        }
        
        geometry.attributes.position.needsUpdate = true;
        plane.rotation.z += 0.002;
      }

      renderer.render(scene, camera);
    };

    animate();

    // Handle resize
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (containerRef.current && rendererRef.current) {
        containerRef.current.removeChild(rendererRef.current.domElement);
      }
      rendererRef.current?.dispose();
    };
  }, [variant]);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 -z-10 opacity-30 dark:opacity-20"
      style={{ pointerEvents: 'none' }}
    />
  );
};

export default ThreeBackground;
