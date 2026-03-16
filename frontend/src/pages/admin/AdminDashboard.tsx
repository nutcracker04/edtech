import { MainLayout } from "@/components/layout/MainLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

const AdminDashboard = () => {
    const navigate = useNavigate();

    const adminActions = [
        {
            title: "PDF Upload & Processing",
            description: "Upload PDF books and start extraction process.",
            path: "/admin/pdf-upload",
            color: "text-blue-500",
            bgColor: "bg-blue-500/10",
            icon: "📄",
        },
        {
            title: "Extraction Management",
            description: "Manage book extraction jobs, review extracted content, and finalize questions.",
            path: "/admin/extractions",
            color: "text-purple-500",
            bgColor: "bg-purple-500/10",
            icon: "📚",
        },
        {
            title: "Admin Panel",
            description: "Manage platform settings and configurations.",
            path: "/admin/settings",
            color: "text-green-500",
            bgColor: "bg-green-500/10",
            icon: "⚙️",
        },
    ];

    return (
        <MainLayout>
            <div className="container py-8">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
                    <p className="text-muted-foreground">Manage platform settings and configurations.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
                    {adminActions.map((action) => (
                        <Card key={action.title} className="hover:shadow-lg transition-shadow border-2 border-border/50">
                            <CardHeader className="flex flex-row items-center gap-4">
                                <div className={`${action.bgColor} ${action.color} p-3 rounded-xl`}>
                                    <div className="h-6 w-6 flex items-center justify-center">
                                        <span className="text-lg">{action.icon}</span>
                                    </div>
                                </div>
                                <div>
                                    <CardTitle>{action.title}</CardTitle>
                                    <CardDescription>{action.description}</CardDescription>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <Button
                                    className="w-full justify-between"
                                    onClick={() => navigate(action.path)}
                                >
                                    Manage {action.title}
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
