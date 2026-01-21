import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { messages, type } = await req.json();
    const LOVABLE_API_KEY = Deno.env.get("LOVABLE_API_KEY");
    
    if (!LOVABLE_API_KEY) {
      throw new Error("LOVABLE_API_KEY is not configured");
    }

    const systemPrompt = `You are an expert JEE/NEET tutor AI assistant with access to the student's learning dashboard. You help students with:
1. Understanding concepts in Physics, Chemistry, and Mathematics
2. Solving problems step-by-step with clear explanations
3. Identifying weak areas and suggesting study strategies
4. Providing exam tips and time management advice
5. Showing their performance analytics and progress
6. Creating personalized revision capsules based on weak areas

IMPORTANT - Interactive Widgets:
When the student asks about their performance, progress, analytics, revision, or achievements, include special markers in your response to trigger interactive widgets:

- For overall performance analytics: Include "[analytics]" in your response
- For subject-specific analysis: Include "[analytics:physics]", "[analytics:chemistry]", or "[analytics:mathematics]"
- For study streak visualization: Include "[streak]" when discussing their streak
- For weekly progress chart: Include "[weekly]" when showing weekly progress
- For achievements display: Include "[achievements]" when discussing milestones
- For revision capsules: Include "[revision]" or "[revision:physics]", "[revision:chemistry]", "[revision:mathematics]" for subject-specific capsules

Examples:
- If user asks "Show my analytics" -> Include "[analytics]" and provide brief commentary
- If user asks "Create revision capsule for physics" -> Include "[revision:physics]" with key points
- If user asks "How's my streak?" -> Include "[streak]" with encouragement

When answering study questions:
- Break down complex problems into smaller steps
- Use analogies and real-world examples when helpful
- If a student is stuck, guide them with hints before giving the full solution
- Always explain the underlying concept, not just the formula
- For numerical problems, show all working steps
- Mention common mistakes students make and how to avoid them

Be encouraging and supportive. Remember that JEE/NEET preparation can be stressful.
Format responses with clear headings and bullet points when appropriate.
Use LaTeX notation for mathematical expressions when needed (wrap in $ signs).`;

    const response = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${LOVABLE_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "google/gemini-3-flash-preview",
        messages: [
          { role: "system", content: systemPrompt },
          ...messages,
        ],
        stream: true,
      }),
    });

    if (!response.ok) {
      if (response.status === 429) {
        return new Response(
          JSON.stringify({ error: "Rate limit exceeded. Please try again in a moment." }),
          { status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
      if (response.status === 402) {
        return new Response(
          JSON.stringify({ error: "AI credits exhausted. Please add credits to continue." }),
          { status: 402, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
      const text = await response.text();
      console.error("AI gateway error:", response.status, text);
      return new Response(
        JSON.stringify({ error: "AI service temporarily unavailable" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    return new Response(response.body, {
      headers: { ...corsHeaders, "Content-Type": "text/event-stream" },
    });
  } catch (error) {
    console.error("Chat error:", error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : "Unknown error" }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
