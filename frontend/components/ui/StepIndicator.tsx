import { motion } from 'framer-motion';

const steps = ['Start', 'Clarify', 'Research', 'Analyze', 'Synthesize', 'Conclude', 'End'];

interface StepIndicatorProps {
  currentState: string;
}

export default function StepIndicator({ currentState }: StepIndicatorProps) {
  const currentStepIndex = steps.indexOf(currentState);

  return (
    <div className="flex justify-between mb-6">
      {steps.map((label, index) => (
        <div key={label} className="flex-1 flex flex-col items-center">
          <motion.div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${
              index < currentStepIndex
                ? 'bg-indigo-600'
                : index === currentStepIndex
                ? 'bg-indigo-600'
                : 'bg-gray-200'
            }`}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: index * 0.1 }}
          >
            {index + 1}
          </motion.div>
          <span className="text-xs mt-2">{label}</span>
        </div>
      ))}
    </div>
  );
}