using UnrealBuildTool;

public class ThumbnailExporter : ModuleRules
{
    public ThumbnailExporter(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicIncludePaths.AddRange(
            new string[] {
                // Add public include paths required here...
            }
        );

        PrivateIncludePaths.AddRange(
            new string[] {
                // Add private include paths required here...
            }
        );

        // Public dependency modules (Modules Unreal Engine needs for the plugin to function)
        PublicDependencyModuleNames.AddRange(
            new string[]
            {
                "Core",
                "CoreUObject",
                "Engine",
                "InputCore",
                "UnrealEd",  // Required for Editor-only functionality
                "Slate",
                "SlateCore",
                "AssetRegistry",
                "EditorStyle",
                "ImageWrapper"
            }
        );

        // Private dependency modules (Internally used Unreal modules)
        PrivateDependencyModuleNames.AddRange(
            new string[]
            {
                "Projects",
                "RenderCore",
                "RHI",
                "ApplicationCore",
                "UnrealEd",  // Add "UnrealEd" to Private Dependencies
                "EditorSubsystem"
            }
        );

        // Dynamically loaded modules (Unreal loads these only when needed)
        DynamicallyLoadedModuleNames.AddRange(
            new string[]
            {
                // Add any modules that your module loads dynamically here...
            }
        );

        // Ensure this is treated as an editor module
        if (Target.Type == TargetRules.TargetType.Editor)
        {
            PrivateDependencyModuleNames.Add("UnrealEd");
        }
    }
}
