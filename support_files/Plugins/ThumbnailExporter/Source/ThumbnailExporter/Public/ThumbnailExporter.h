#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "UObject/Object.h"
#include "ThumbnailExporter.generated.h"

/**
 * Main module class for the ThumbnailExporter plugin.
 */
class FThumbnailExporterModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};

/**
 * UObject class that exposes logging functions to Blueprints and Python.
 */
UCLASS()
class THUMBNAILEXPORTER_API UThumbnailExporter : public UObject
{
    GENERATED_BODY()

public:
    /** Function to test logging */
    UFUNCTION(BlueprintCallable, Category = "Thumbnails")
    static void PrintTestMessage();

    /** Function to export an asset's thumbnail as a PNG file */
    UFUNCTION(BlueprintCallable, Category = "Thumbnails")
    static void ExportThumbnailAsPNG(FString ObjectPath, FString OutputPath);
};
