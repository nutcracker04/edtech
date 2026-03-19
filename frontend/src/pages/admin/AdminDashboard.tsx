import { MainLayout } from "@/components/layout/MainLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

const AdminDashboard = () => {
    const navigate = useNavigate();

    const adminActions = [
        {
            title: "Questions",
            description:
                "Import batches (JSON or form), open any batch, then edit, delete, reject, or approve into the question bank — one flow.",
            path: "/admin/questions",
            color: "text-primary",
            bgColor: "bg-primary/10",
            icon: "📋",
        },
        {
            title: "Settings",
            description: "Your profile and application preferences.",
            path: "/settings",
            color: "text-muted-foreground",
            bgColor: "bg-muted",
            icon: "⚙️",
        },
    ];

    return (
        <MainLayout>
            <div className="container py-8">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Admin</h1>
                    <p className="text-muted-foreground">
                        Tools for managing content. Start with <strong>Questions</strong> to dump and review data.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl">
                    {adminActions.map((action) => (
                        <Card key={action.title} className="hover:shadow-md transition-shadow border-2 border-border/50">
                            <CardHeader className="flex flex-row items-center gap-4">
                                <div className={`${action.bgColor} ${action.color} p-3 rounded-xl`}>
                                    <span className="text-lg">{action.icon}</span>
                                </div>
                                <div>
                                    <CardTitle>{action.title}</CardTitle>
                                    <CardDescription>{action.description}</CardDescription>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <Button
                                    className="w-full justify-between"
                                    variant={action.title === "Questions" ? "default" : "outline"}
                                    onClick={() => navigate(action.path)}
                                >
                                    Open
                                    <ArrowRight className="h-4 w-4 ml-2" />
                                </Button>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </MainLayout>
    );
};

export default AdminDashboard;
