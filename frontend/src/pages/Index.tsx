import { MainLayout } from "@/components/layout/MainLayout";
import { QuestionInput } from "@/components/home/QuestionInput";

const Index = () => {
  return (
    <MainLayout>
      <div className="min-h-screen flex flex-col px-4 sm:px-6 py-2 sm:py-3 lg:py-4">
        <QuestionInput />
      </div>
    </MainLayout>
  );
};

export default Index;
