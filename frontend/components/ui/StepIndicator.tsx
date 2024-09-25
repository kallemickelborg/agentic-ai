import { motion } from 'framer-motion';

const steps = ['Init', 'Clarify', 'Research', 'Analyze', 'Synthesize', 'Conclude', 'End'];

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
                ? 'bg-green-500'
                : index === currentStepIndex
                ? 'bg-blue-500'
                : 'bg-gray-400'
            }`}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: index * 0.1 }}
          >
            {index + 1}
          </motion.div>
          <span className="text-sm mt-2">{label}</span>
        </div>
      ))}
    </div>
  );
}