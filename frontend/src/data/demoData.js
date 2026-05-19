export const DEMO_EXAMS = [
  { id:1, name:'CS301 — Midterm', course:'Data Structures', date:'Nov 14, 2024', papers:48, status:'processing', progress:72, flagged:3, graded:34 },
  { id:2, name:'MATH202 — Final',  course:'Linear Algebra',  date:'Dec 05, 2024', papers:62, status:'review',     progress:100, flagged:5, graded:62 },
  { id:3, name:'PHY101 — Quiz 3',  course:'Mechanics',       date:'Oct 22, 2024', papers:35, status:'complete',   progress:100, flagged:1, graded:35 },
  { id:4, name:'CS401 — Final',    course:'Algorithms',      date:'Dec 12, 2024', papers:55, status:'pending',    progress:0,   flagged:0, graded:0  },
];

export const DEMO_QUEUE = [
  {
    id:1, student:'Student #A-047', exam:'CS301 — Midterm',
    question:'Q2: Explain the time complexity of merge sort and justify your answer.',
    maxScore:10, aiScore:8, confidence:0.91,
    handwriting:`Merge sort has O(n log n) time complexity. This is because the
algorithm divides the array into 2 halves recursively, giving us
log n levels of recursion. At each level we do O(n) work to merge
the subarrays back together.

T(n) = 2T(n/2) + O(n)
     = O(n log n)    [by Master Theorem case 2]

The algorithm is efficient for large datasets even in the worst
case, unlike quicksort which can degrade to O(n²).`,
    justification:`Student correctly identifies O(n log n) time complexity and provides the recurrence relation T(n) = 2T(n/2) + O(n) with correct Master Theorem application. Full marks for time complexity analysis (8/8). Deducted 2 points: rubric criterion 3b requires discussion of O(n) auxiliary space complexity for the merge operation — this is absent from the answer.`,
    flagged:false,
    rubricCriteria:[
      { label:'Correct complexity stated',       pts:3, awarded:3 },
      { label:'Recurrence relation shown',       pts:3, awarded:3 },
      { label:'Master Theorem or proof',         pts:2, awarded:2 },
      { label:'Space complexity discussion',     pts:2, awarded:0 },
    ],
  },
  {
    id:2, student:'Student #B-019', exam:'CS301 — Midterm',
    question:'Q3: Prove by induction that 1 + 2 + ... + n = n(n+1)/2.',
    maxScore:15, aiScore:12, confidence:0.85,
    handwriting:`Proof by Mathematical Induction.

Base case: n=1. LHS = 1. RHS = 1(1+1)/2 = 1. ✓

Inductive step: Assume true for n=k.
i.e. 1+2+...+k = k(k+1)/2

Need to show: 1+2+...+k+(k+1) = (k+1)(k+2)/2

LHS = k(k+1)/2 + (k+1)
    = (k+1)[k/2 + 1]
    = (k+1)(k+2)/2  = RHS ✓

Therefore true for all n ≥ 1 by induction. □`,
    justification:`Base case is correctly established. Inductive hypothesis is stated but not explicitly labeled before use — minor notational deduction per rubric 2c (-1pt). The algebraic manipulation in the inductive step is clean and correct. Conclusion is properly stated. -2 additional points: student did not state the claim to prove at the start of the inductive step explicitly enough for full formal credit per rubric 2d.`,
    flagged:true,
    flagReason:'Proof structure closely mirrors Student #B-022 (similarity score 0.88). Review recommended.',
    rubricCriteria:[
      { label:'Base case correct',               pts:3, awarded:3 },
      { label:'Inductive hypothesis stated',     pts:3, awarded:2 },
      { label:'Algebraic manipulation correct',  pts:5, awarded:5 },
      { label:'Formal conclusion',               pts:2, awarded:2 },
      { label:'Overall clarity & notation',      pts:2, awarded:0 },
    ],
  },
  {
    id:3, student:'Student #C-031', exam:'CS301 — Midterm',
    question:'Q1: What is a binary search tree? State its invariant.',
    maxScore:8, aiScore:6, confidence:0.78,
    handwriting:`A BST is a binary tree where every node has a key.
For any node N: all keys in the left subtree are less than N,
and all keys in the right subtree are greater than N.

This property holds recursively for all subtrees.
Search, insert, delete are O(h) where h is height.`,
    justification:`Definition is correct and the BST invariant is accurately stated. Student correctly notes recursive nature. -2 points: rubric requires mention of the equal-key policy (duplicates) — student's answer implies strict inequality but does not explicitly address how duplicates are handled (criterion 1c). Operation complexity mention earns no extra credit as it wasn't part of the rubric for this question.`,
    flagged:false,
    rubricCriteria:[
      { label:'Correct definition of BST',      pts:3, awarded:3 },
      { label:'Invariant stated correctly',     pts:3, awarded:3 },
      { label:'Duplicate/equal-key policy',     pts:2, awarded:0 },
    ],
  },
];

// ─── Shared sub-components ────────────────────────────────────────────────
