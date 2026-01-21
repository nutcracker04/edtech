import {
  Question,
  Subject,
  Difficulty,
  Grade,
  TopicMastery,
  CapsuleTopic,
  PerformanceMetrics,
} from '@/types';

// ============================================================================
// PHYSICS QUESTIONS
// ============================================================================

const physicsQuestions: Question[] = [
  // Kinematics (Grade 11-12)
  {
    id: 'physics-1',
    question: 'A particle moves in a straight line with initial velocity 5 m/s and constant acceleration 2 m/s². What is the velocity after 3 seconds?',
    options: [
      { id: 'a', text: '8 m/s' },
      { id: 'b', text: '10 m/s' },
      { id: 'c', text: '11 m/s' },
      { id: 'd', text: '15 m/s' },
    ],
    correctAnswer: 'c',
    explanation: 'Using the equation v = u + at, where u = 5 m/s, a = 2 m/s², and t = 3s: v = 5 + (2 × 3) = 5 + 6 = 11 m/s',
    difficulty: 'easy',
    topic: 'Kinematics',
    subject: 'physics',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'physics-2',
    question: 'A car starts from rest and accelerates uniformly at 3 m/s² for 5 seconds. What is the distance covered?',
    options: [
      { id: 'a', text: '15 m' },
      { id: 'b', text: '37.5 m' },
      { id: 'c', text: '75 m' },
      { id: 'd', text: '150 m' },
    ],
    correctAnswer: 'b',
    explanation: 'Using s = ut + ½at², where u = 0, a = 3 m/s², t = 5s: s = 0 + ½(3)(5²) = 1.5 × 25 = 37.5 m',
    difficulty: 'easy',
    topic: 'Kinematics',
    subject: 'physics',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'physics-3',
    question: 'An object is projected upward with initial velocity 20 m/s. Taking g = 10 m/s², what is the maximum height reached?',
    options: [
      { id: 'a', text: '10 m' },
      { id: 'b', text: '20 m' },
      { id: 'c', text: '30 m' },
      { id: 'd', text: '40 m' },
    ],
    correctAnswer: 'b',
    explanation: 'At maximum height, v = 0. Using v² = u² - 2gh: 0 = (20)² - 2(10)h, so h = 400/20 = 20 m',
    difficulty: 'medium',
    topic: 'Kinematics',
    subject: 'physics',
    gradeLevel: ['11', '12'],
  },

  // Mechanics (Grade 11-12)
  {
    id: 'physics-4',
    question: 'A force of 10 N is applied to a 2 kg object. What is the acceleration produced?',
    options: [
      { id: 'a', text: '2 m/s²' },
      { id: 'b', text: '5 m/s²' },
      { id: 'c', text: '10 m/s²' },
      { id: 'd', text: '20 m/s²' },
    ],
    correctAnswer: 'b',
    explanation: 'Using F = ma: a = F/m = 10/2 = 5 m/s²',
    difficulty: 'easy',
    topic: 'Mechanics',
    subject: 'physics',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'physics-5',
    question: 'Two blocks of masses m₁ = 3 kg and m₂ = 2 kg are in contact on a frictionless surface. A force of 10 N is applied to m₁. What is the acceleration of the system?',
    options: [
      { id: 'a', text: '1 m/s²' },
      { id: 'b', text: '2 m/s²' },
      { id: 'c', text: '3 m/s²' },
      { id: 'd', text: '5 m/s²' },
    ],
    correctAnswer: 'b',
    explanation: 'Total mass = 3 + 2 = 5 kg. Using F = ma: a = F/(m₁+m₂) = 10/5 = 2 m/s²',
    difficulty: 'medium',
    topic: 'Mechanics',
    subject: 'physics',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'physics-6',
    question: 'A block of mass 5 kg is pulled across a horizontal surface by a rope at an angle of 30° with horizontal. If the tension is 20 N and coefficient of friction is 0.1, what is the acceleration? (g = 10 m/s²)',
    options: [
      { id: 'a', text: '2.3 m/s²' },
      { id: 'b', text: '3.2 m/s²' },
      { id: 'c', text: '2.8 m/s²' },
      { id: 'd', text: '3.5 m/s²' },
    ],
    correctAnswer: 'a',
    explanation: 'Horizontal component of tension = 20cos(30°) = 20(√3/2) ≈ 17.32 N. Friction = μ(mg - 20sin30°) = 0.1(50 - 10) = 4 N. Net force = 17.32 - 4 = 13.32 N. a = 13.32/5 ≈ 2.3 m/s²',
    difficulty: 'hard',
    topic: 'Mechanics',
    subject: 'physics',
    gradeLevel: ['12'],
  },

  // Thermodynamics (Grade 11-12)
  {
    id: 'physics-7',
    question: 'In an isothermal process, what happens to the temperature of a gas?',
    options: [
      { id: 'a', text: 'Increases' },
      { id: 'b', text: 'Decreases' },
      { id: 'c', text: 'Remains constant' },
      { id: 'd', text: 'Becomes zero' },
    ],
    correctAnswer: 'c',
    explanation: 'In an isothermal process, the temperature of the gas remains constant by definition. The internal energy also remains constant, so ΔU = 0.',
    difficulty: 'easy',
    topic: 'Thermodynamics',
    subject: 'physics',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'physics-8',
    question: '1 mole of ideal gas undergoes an isothermal expansion at 300 K from volume 1 L to 10 L. What is the work done by the gas? (R = 8.314 J/mol·K)',
    options: [
      { id: 'a', text: '5.76 kJ' },
      { id: 'b', text: '5.76 J' },
      { id: 'c', text: '57.6 J' },
      { id: 'd', text: '0 J' },
    ],
    correctAnswer: 'a',
    explanation: 'For isothermal process: W = nRT ln(V₂/V₁) = 1 × 8.314 × 300 × ln(10) = 2494.2 × 2.303 ≈ 5745 J ≈ 5.76 kJ',
    difficulty: 'medium',
    topic: 'Thermodynamics',
    subject: 'physics',
    gradeLevel: ['12'],
  },
  {
    id: 'physics-9',
    question: 'What is the first law of thermodynamics?',
    options: [
      { id: 'a', text: 'ΔU = Q - W' },
      { id: 'b', text: 'ΔU = Q + W' },
      { id: 'c', text: 'Q = W' },
      { id: 'd', text: 'ΔU = 0' },
    ],
    correctAnswer: 'a',
    explanation: 'The first law of thermodynamics states that ΔU = Q - W, where ΔU is change in internal energy, Q is heat added, and W is work done by the system.',
    difficulty: 'easy',
    topic: 'Thermodynamics',
    subject: 'physics',
    gradeLevel: ['11', '12'],
  },

  // Electromagnetism (Grade 12)
  {
    id: 'physics-10',
    question: 'What is the magnetic force on a current-carrying conductor in a magnetic field?',
    options: [
      { id: 'a', text: 'F = BIL' },
      { id: 'b', text: 'F = BIL sin(θ)' },
      { id: 'c', text: 'F = BI/L' },
      { id: 'd', text: 'F = BL/I' },
    ],
    correctAnswer: 'b',
    explanation: 'The magnetic force on a current-carrying conductor is F = BIL sin(θ), where B is magnetic field, I is current, L is length, and θ is angle between conductor and field.',
    difficulty: 'easy',
    topic: 'Electromagnetism',
    subject: 'physics',
    gradeLevel: ['12'],
  },
  {
    id: 'physics-11',
    question: 'A conductor of length 0.5 m carrying current 2 A is placed perpendicular to a magnetic field of 0.4 T. What is the force on the conductor?',
    options: [
      { id: 'a', text: '0.2 N' },
      { id: 'b', text: '0.4 N' },
      { id: 'c', text: '0.8 N' },
      { id: 'd', text: '1.6 N' },
    ],
    correctAnswer: 'b',
    explanation: 'F = BIL sin(90°) = 0.4 × 2 × 0.5 × 1 = 0.4 N',
    difficulty: 'easy',
    topic: 'Electromagnetism',
    subject: 'physics',
    gradeLevel: ['12'],
  },

  // Modern Physics (Grade 12)
  {
    id: 'physics-12',
    question: 'The photoelectric effect is best explained by which theory?',
    options: [
      { id: 'a', text: 'Wave theory of light' },
      { id: 'b', text: 'Particle theory of light (Photon theory)' },
      { id: 'c', text: 'Classical mechanics' },
      { id: 'd', text: 'Quantum mechanics' },
    ],
    correctAnswer: 'b',
    explanation: 'The photoelectric effect is best explained by Einstein\'s photon theory, where light consists of discrete particles (photons) with energy E = hf.',
    difficulty: 'medium',
    topic: 'Modern Physics',
    subject: 'physics',
    gradeLevel: ['12'],
  },
];

// ============================================================================
// CHEMISTRY QUESTIONS
// ============================================================================

const chemistryQuestions: Question[] = [
  // Organic Chemistry (Grade 11-12)
  {
    id: 'chem-1',
    question: 'What is the IUPAC name of CH₃-CH₂-CH₂-CH₃?',
    options: [
      { id: 'a', text: 'Methane' },
      { id: 'b', text: 'Butane' },
      { id: 'c', text: 'Propane' },
      { id: 'd', text: 'Pentane' },
    ],
    correctAnswer: 'b',
    explanation: 'The compound has 4 carbon atoms in a straight chain, so it is butane (C₄H₁₀).',
    difficulty: 'easy',
    topic: 'Organic Chemistry',
    subject: 'chemistry',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'chem-2',
    question: 'Which functional group is present in alcohols?',
    options: [
      { id: 'a', text: '-COOH' },
      { id: 'b', text: '-OH' },
      { id: 'c', text: '-CHO' },
      { id: 'd', text: '-NH₂' },
    ],
    correctAnswer: 'b',
    explanation: 'Alcohols contain the hydroxyl functional group (-OH) attached to a carbon atom.',
    difficulty: 'easy',
    topic: 'Organic Chemistry',
    subject: 'chemistry',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'chem-3',
    question: 'What is the product of the oxidation of ethanol?',
    options: [
      { id: 'a', text: 'Methane' },
      { id: 'b', text: 'Acetaldehyde' },
      { id: 'c', text: 'Methanol' },
      { id: 'd', text: 'Acetone' },
    ],
    correctAnswer: 'b',
    explanation: 'Ethanol (C₂H₅OH) when oxidized with mild oxidizing agents produces acetaldehyde (CH₃CHO).',
    difficulty: 'medium',
    topic: 'Organic Chemistry',
    subject: 'chemistry',
    gradeLevel: ['11', '12'],
  },

  // Inorganic Chemistry (Grade 11-12)
  {
    id: 'chem-4',
    question: 'What is the valency of sulfur in H₂SO₄?',
    options: [
      { id: 'a', text: '+2' },
      { id: 'b', text: '+4' },
      { id: 'c', text: '+6' },
      { id: 'd', text: '-2' },
    ],
    correctAnswer: 'c',
    explanation: 'In H₂SO₄, sulfur exhibits +6 oxidation state as it forms six bonds (4 with O and 2 coordinate bonds).',
    difficulty: 'medium',
    topic: 'Inorganic Chemistry',
    subject: 'chemistry',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'chem-5',
    question: 'Which of the following is an amphoteric oxide?',
    options: [
      { id: 'a', text: 'Na₂O' },
      { id: 'b', text: 'Al₂O₃' },
      { id: 'c', text: 'SiO₂' },
      { id: 'd', text: 'Cl₂O₇' },
    ],
    correctAnswer: 'b',
    explanation: 'Al₂O₃ is amphoteric because it reacts with both acids and bases: Al₂O₃ + 2NaOH + 3H₂O → 2NaAl(OH)₄',
    difficulty: 'medium',
    topic: 'Inorganic Chemistry',
    subject: 'chemistry',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'chem-6',
    question: 'What is the electronic configuration of Fe³⁺ (atomic number of Fe = 26)?',
    options: [
      { id: 'a', text: '[Ar] 3d⁶' },
      { id: 'b', text: '[Ar] 3d⁵' },
      { id: 'c', text: '[Ar] 3d⁷' },
      { id: 'd', text: '[Ar] 3d⁴' },
    ],
    correctAnswer: 'b',
    explanation: 'Fe has atomic number 26: [Ar] 3d⁶ 4s². Fe³⁺ loses 3 electrons (2 from 4s and 1 from 3d): [Ar] 3d⁵',
    difficulty: 'medium',
    topic: 'Inorganic Chemistry',
    subject: 'chemistry',
    gradeLevel: ['12'],
  },

  // Physical Chemistry (Grade 11-12)
  {
    id: 'chem-7',
    question: 'What is the pH of a neutral solution at 25°C?',
    options: [
      { id: 'a', text: '0' },
      { id: 'b', text: '7' },
      { id: 'c', text: '14' },
      { id: 'd', text: '1' },
    ],
    correctAnswer: 'b',
    explanation: 'At 25°C, Kw = 1 × 10⁻¹⁴, so pH = 7 for a neutral solution where [H⁺] = [OH⁻] = 1 × 10⁻⁷ M.',
    difficulty: 'easy',
    topic: 'Physical Chemistry',
    subject: 'chemistry',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'chem-8',
    question: 'A solution has [H⁺] = 1 × 10⁻³ M. What is its pH?',
    options: [
      { id: 'a', text: '1' },
      { id: 'b', text: '2' },
      { id: 'c', text: '3' },
      { id: 'd', text: '4' },
    ],
    correctAnswer: 'c',
    explanation: 'pH = -log[H⁺] = -log(1 × 10⁻³) = -(-3) = 3',
    difficulty: 'easy',
    topic: 'Physical Chemistry',
    subject: 'chemistry',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'chem-9',
    question: 'What is the order of reaction if the rate equation is: Rate = k[A][B]²?',
    options: [
      { id: 'a', text: '0' },
      { id: 'b', text: '1' },
      { id: 'c', text: '2' },
      { id: 'd', text: '3' },
    ],
    correctAnswer: 'd',
    explanation: 'Order of reaction = sum of powers of concentration terms = 1 + 2 = 3 (third order)',
    difficulty: 'medium',
    topic: 'Physical Chemistry',
    subject: 'chemistry',
    gradeLevel: ['12'],
  },

  // Electrochemistry (Grade 12)
  {
    id: 'chem-10',
    question: 'What is the standard electrode potential for a hydrogen electrode?',
    options: [
      { id: 'a', text: '+1 V' },
      { id: 'b', text: '-1 V' },
      { id: 'c', text: '0 V' },
      { id: 'd', text: '+2 V' },
    ],
    correctAnswer: 'c',
    explanation: 'The standard hydrogen electrode (SHE) is assigned a potential of 0 V by convention, and it serves as reference for all electrode potentials.',
    difficulty: 'easy',
    topic: 'Electrochemistry',
    subject: 'chemistry',
    gradeLevel: ['12'],
  },
];

// ============================================================================
// MATHEMATICS QUESTIONS
// ============================================================================

const mathematicsQuestions: Question[] = [
  // Calculus - Differentiation (Grade 11-12)
  {
    id: 'math-1',
    question: 'What is the derivative of x³ with respect to x?',
    options: [
      { id: 'a', text: 'x²' },
      { id: 'b', text: '3x²' },
      { id: 'c', text: '3x' },
      { id: 'd', text: 'x³' },
    ],
    correctAnswer: 'b',
    explanation: 'Using the power rule: d/dx(x³) = 3x²',
    difficulty: 'easy',
    topic: 'Calculus',
    subject: 'mathematics',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'math-2',
    question: 'Find the derivative of sin(x).',
    options: [
      { id: 'a', text: 'cos(x)' },
      { id: 'b', text: '-cos(x)' },
      { id: 'c', text: 'sin(x)' },
      { id: 'd', text: 'tan(x)' },
    ],
    correctAnswer: 'a',
    explanation: 'd/dx(sin(x)) = cos(x)',
    difficulty: 'easy',
    topic: 'Calculus',
    subject: 'mathematics',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'math-3',
    question: 'Find the derivative of e^(2x).',
    options: [
      { id: 'a', text: 'e^(2x)' },
      { id: 'b', text: '2e^(2x)' },
      { id: 'c', text: 'e^x' },
      { id: 'd', text: '2xe^(2x)' },
    ],
    correctAnswer: 'b',
    explanation: 'Using chain rule: d/dx(e^(2x)) = e^(2x) × 2 = 2e^(2x)',
    difficulty: 'easy',
    topic: 'Calculus',
    subject: 'mathematics',
    gradeLevel: ['12'],
  },

  // Calculus - Integration (Grade 12)
  {
    id: 'math-4',
    question: 'What is the indefinite integral of x² dx?',
    options: [
      { id: 'a', text: 'x³ + C' },
      { id: 'b', text: '(x³/3) + C' },
      { id: 'c', text: '2x + C' },
      { id: 'd', text: 'x² + C' },
    ],
    correctAnswer: 'b',
    explanation: '∫x² dx = (x³/3) + C (using power rule for integration)',
    difficulty: 'easy',
    topic: 'Calculus',
    subject: 'mathematics',
    gradeLevel: ['12'],
  },
  {
    id: 'math-5',
    question: 'Integrate: ∫sin(x) dx',
    options: [
      { id: 'a', text: 'cos(x) + C' },
      { id: 'b', text: '-cos(x) + C' },
      { id: 'c', text: 'sin(x) + C' },
      { id: 'd', text: 'tan(x) + C' },
    ],
    correctAnswer: 'b',
    explanation: '∫sin(x) dx = -cos(x) + C',
    difficulty: 'easy',
    topic: 'Calculus',
    subject: 'mathematics',
    gradeLevel: ['12'],
  },
  {
    id: 'math-6',
    question: 'Find ∫₀¹ x² dx',
    options: [
      { id: 'a', text: '1/2' },
      { id: 'b', text: '1/3' },
      { id: 'c', text: '1/4' },
      { id: 'd', text: '2/3' },
    ],
    correctAnswer: 'b',
    explanation: '∫₀¹ x² dx = [x³/3]₀¹ = 1/3 - 0 = 1/3',
    difficulty: 'medium',
    topic: 'Calculus',
    subject: 'mathematics',
    gradeLevel: ['12'],
  },

  // Algebra (Grade 11-12)
  {
    id: 'math-7',
    question: 'Solve the equation: 2x + 5 = 13',
    options: [
      { id: 'a', text: 'x = 2' },
      { id: 'b', text: 'x = 3' },
      { id: 'c', text: 'x = 4' },
      { id: 'd', text: 'x = 5' },
    ],
    correctAnswer: 'c',
    explanation: '2x + 5 = 13 → 2x = 8 → x = 4',
    difficulty: 'easy',
    topic: 'Algebra',
    subject: 'mathematics',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'math-8',
    question: 'If x² + 3x + 2 = 0, what are the roots?',
    options: [
      { id: 'a', text: 'x = 1, -2' },
      { id: 'b', text: 'x = -1, -2' },
      { id: 'c', text: 'x = 2, -1' },
      { id: 'd', text: 'x = 1, 2' },
    ],
    correctAnswer: 'b',
    explanation: 'x² + 3x + 2 = (x + 1)(x + 2) = 0, so x = -1 or x = -2',
    difficulty: 'medium',
    topic: 'Algebra',
    subject: 'mathematics',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'math-9',
    question: 'What is the sum of the roots of 3x² - 6x + 2 = 0?',
    options: [
      { id: 'a', text: '1' },
      { id: 'b', text: '2' },
      { id: 'c', text: '-2' },
      { id: 'd', text: '3' },
    ],
    correctAnswer: 'b',
    explanation: 'For ax² + bx + c = 0, sum of roots = -b/a = -(-6)/3 = 2',
    difficulty: 'medium',
    topic: 'Algebra',
    subject: 'mathematics',
    gradeLevel: ['11', '12'],
  },

  // Trigonometry (Grade 11-12)
  {
    id: 'math-10',
    question: 'What is sin(30°)?',
    options: [
      { id: 'a', text: '0' },
      { id: 'b', text: '1/2' },
      { id: 'c', text: '√3/2' },
      { id: 'd', text: '1' },
    ],
    correctAnswer: 'b',
    explanation: 'sin(30°) = 1/2 (standard trigonometric value)',
    difficulty: 'easy',
    topic: 'Trigonometry',
    subject: 'mathematics',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'math-11',
    question: 'Find cos(60°).',
    options: [
      { id: 'a', text: '0' },
      { id: 'b', text: '1/2' },
      { id: 'c', text: '√3/2' },
      { id: 'd', text: '1' },
    ],
    correctAnswer: 'b',
    explanation: 'cos(60°) = 1/2 (standard trigonometric value)',
    difficulty: 'easy',
    topic: 'Trigonometry',
    subject: 'mathematics',
    gradeLevel: ['11', '12'],
  },
  {
    id: 'math-12',
    question: 'What is tan(45°)?',
    options: [
      { id: 'a', text: '0' },
      { id: 'b', text: '1' },
      { id: 'c', text: '√3' },
      { id: 'd', text: '1/√3' },
    ],
    correctAnswer: 'b',
    explanation: 'tan(45°) = 1 (standard trigonometric value)',
    difficulty: 'easy',
    topic: 'Trigonometry',
    subject: 'mathematics',
    gradeLevel: ['11', '12'],
  },

  // Probability & Statistics (Grade 12)
  {
    id: 'math-13',
    question: 'What is the probability of getting a head when flipping a fair coin?',
    options: [
      { id: 'a', text: '0' },
      { id: 'b', text: '1/2' },
      { id: 'c', text: '1/3' },
      { id: 'd', text: '1' },
    ],
    correctAnswer: 'b',
    explanation: 'A fair coin has two equally likely outcomes (head or tail), so P(head) = 1/2',
    difficulty: 'easy',
    topic: 'Probability',
    subject: 'mathematics',
    gradeLevel: ['12'],
  },
];

// ============================================================================
// Question Bank Service
// ============================================================================

const allQuestions = [...physicsQuestions, ...chemistryQuestions, ...mathematicsQuestions];

export const questionBankService = {
  /**
   * Get all questions
   */
  getAllQuestions(): Question[] {
    return [...allQuestions];
  },

  /**
   * Get questions by subject
   */
  getQuestionsBySubject(subject: Subject, limit?: number): Question[] {
    const filtered = allQuestions.filter(q => q.subject === subject);
    return limit ? filtered.slice(0, limit) : filtered;
  },

  /**
   * Get questions by topic
   */
  getQuestionsByTopic(topic: string, limit?: number): Question[] {
    const filtered = allQuestions.filter(q => q.topic === topic);
    return limit ? filtered.slice(0, limit) : filtered;
  },

  /**
   * Get questions by difficulty
   */
  getQuestionsByDifficulty(difficulty: Difficulty, limit?: number): Question[] {
    const filtered = allQuestions.filter(q => q.difficulty === difficulty);
    return limit ? filtered.slice(0, limit) : filtered;
  },

  /**
   * Get questions by grade level
   */
  getQuestionsByGrade(grade: Grade, limit?: number): Question[] {
    const filtered = allQuestions.filter(q => q.gradeLevel.includes(grade));
    return limit ? filtered.slice(0, limit) : filtered;
  },

  /**
   * Get questions by multiple criteria
   */
  getQuestionsFiltered(options: {
    subject?: Subject;
    topic?: string;
    difficulty?: Difficulty;
    grade?: Grade;
    limit?: number;
  }): Question[] {
    let filtered = allQuestions;

    if (options.subject) {
      filtered = filtered.filter(q => q.subject === options.subject);
    }
    if (options.topic) {
      filtered = filtered.filter(q => q.topic === options.topic);
    }
    if (options.difficulty) {
      filtered = filtered.filter(q => q.difficulty === options.difficulty);
    }
    if (options.grade) {
      filtered = filtered.filter(q => q.gradeLevel.includes(options.grade!));
    }

    return options.limit ? filtered.slice(0, options.limit) : filtered;
  },

  /**
   * Get a random question
   */
  getRandomQuestion(): Question {
    return allQuestions[Math.floor(Math.random() * allQuestions.length)];
  },

  /**
   * Get random questions
   */
  getRandomQuestions(count: number): Question[] {
    const shuffled = [...allQuestions].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, count);
  },

  /**
   * Get questions by subject and difficulty distribution
   */
  getQuestionsByDistribution(
    subjectQuestionCounts: Record<Subject, number>,
    difficultyDistribution?: Record<Difficulty, number>
  ): Question[] {
    const result: Question[] = [];

    for (const [subject, count] of Object.entries(subjectQuestionCounts) as [Subject, number][]) {
      const subjectQuestions = this.getQuestionsBySubject(subject);

      if (difficultyDistribution) {
        // Distribute by difficulty
        let added = 0;
        for (const [difficulty, diffCount] of Object.entries(difficultyDistribution) as [Difficulty, number][]) {
          const diffQuestions = subjectQuestions.filter(q => q.difficulty === difficulty);
          const toAdd = Math.min(diffCount, diffQuestions.length, count - added);
          result.push(...diffQuestions.slice(0, toAdd));
          added += toAdd;
        }
      } else {
        // Just get random questions from subject
        const shuffled = subjectQuestions.sort(() => Math.random() - 0.5);
        result.push(...shuffled.slice(0, count));
      }
    }

    return result;
  },

  /**
   * Get all unique topics
   */
  getTopics(subject?: Subject): string[] {
    const filtered = subject
      ? allQuestions.filter(q => q.subject === subject)
      : allQuestions;

    return [...new Set(filtered.map(q => q.topic))];
  },

  /**
   * Get all unique subjects
   */
  getSubjects(): Subject[] {
    return [...new Set(allQuestions.map(q => q.subject))] as Subject[];
  },

  /**
   * Get question by ID
   */
  getQuestionById(id: string): Question | undefined {
    return allQuestions.find(q => q.id === id);
  },

  /**
   * Get total question count
   */
  getTotalQuestionCount(): number {
    return allQuestions.length;
  },

  /**
   * Get question count by subject
   */
  getQuestionCountBySubject(): Record<Subject, number> {
    return {
      physics: this.getQuestionsBySubject('physics').length,
      chemistry: this.getQuestionsBySubject('chemistry').length,
      mathematics: this.getQuestionsBySubject('mathematics').length,
    };
  },
};
