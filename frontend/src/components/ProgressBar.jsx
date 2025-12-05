
const ProgressBar = ({ current, target, label }) => {
  const percentage = Math.min(Math.max((current / target) * 100, 0), 100);
  
  return (
    <div className="w-full bg-gray-700 rounded-full h-6 mb-4 relative overflow-hidden">
      <div 
        className={`h-6 rounded-full transition-all duration-500 ease-out ${percentage >= 100 ? 'bg-green-500' : 'bg-blue-500'}`}
        style={{ width: `${percentage}%` }}
      ></div>
      <div className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white drop-shadow-md">
        {label}: {percentage.toFixed(1)}%
      </div>
    </div>
  );
};

export default ProgressBar;
