import { MainLayout } from "@/components/layout/MainLayout";
import { MistakesAnalysis } from "@/components/dashboard/mistakes/MistakesAnalysis";

const Mistakes = () => {
    return (
        <MainLayout>
            <div className="p-4 sm:p-6 lg:p-8 animate-fade-in space-y-6">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Mistakes</h1>
                    <p className="text-sm text-muted-foreground">Analyze your errors across chapters and subjects</p>
                </div>

                <div className="animate-slide-up">
                    <MistakesAnalysis />
                </div>
            </div>
        </MainLayout>
    );
};

export default Mistakes;
