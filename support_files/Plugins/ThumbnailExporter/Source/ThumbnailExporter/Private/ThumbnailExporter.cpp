#include "ThumbnailExporter.h"
#include "Modules/ModuleManager.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "IImageWrapperModule.h"
#include "IImageWrapper.h"
#include "ThumbnailRendering/ThumbnailManager.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "UnrealEd.h"
#include "ObjectTools.h"

#define LOCTEXT_NAMESPACE "FThumbnailExporterModule"

void FThumbnailExporterModule::StartupModule()
{
    UE_LOG(LogTemp, Warning, TEXT("ThumbnailExporter Plugin Loaded Successfully!"));
}

void FThumbnailExporterModule::ShutdownModule()
{
    UE_LOG(LogTemp, Warning, TEXT("ThumbnailExporter Plugin Unloaded!"));
}

#undef LOCTEXT_NAMESPACE
IMPLEMENT_MODULE(FThumbnailExporterModule, ThumbnailExporter)

void UThumbnailExporter::PrintTestMessage()
{
    UE_LOG(LogTemp, Warning, TEXT("ThumbnailExporter Test Message: Plugin is Active and Working!"));
}

void UThumbnailExporter::ExportThumbnailAsPNG(FString ObjectPath, FString OutputPath)
{
    if (ObjectPath.IsEmpty() || OutputPath.IsEmpty())
    {
        UE_LOG(LogTemp, Warning, TEXT("Invalid input parameters!"));
        return;
    }

    // Use JPG extension
    FString NewOutputPath = FPaths::ChangeExtension(OutputPath, TEXT(".jpg"));
    
    // Load the asset
    FAssetRegistryModule& AssetRegistryModule = FModuleManager::Get().LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
    FAssetData AssetData = AssetRegistryModule.Get().GetAssetByObjectPath(FName(*ObjectPath));
    UObject* MyObject = AssetData.GetAsset();

    if (!MyObject)
    {
        UE_LOG(LogTemp, Warning, TEXT("Asset not found at path: %s"), *ObjectPath);
        return;
    }

    // Render the thumbnail
    const int32 ThumbnailSize = 256;
    FObjectThumbnail ObjectThumbnail;
    
    ThumbnailTools::RenderThumbnail(
        MyObject,
        ThumbnailSize,
        ThumbnailSize,
        ThumbnailTools::EThumbnailTextureFlushMode::AlwaysFlush,
        nullptr,
        &ObjectThumbnail
    );

    if (ObjectThumbnail.GetUncompressedImageData().Num() == 0)
    {
        UE_LOG(LogTemp, Warning, TEXT("No thumbnail data for asset: %s"), *ObjectPath);
        return;
    }

    // Create JPG image
    IImageWrapperModule& ImageWrapperModule = FModuleManager::Get().LoadModuleChecked<IImageWrapperModule>(TEXT("ImageWrapper"));
    TSharedPtr<IImageWrapper> ImageWrapper = ImageWrapperModule.CreateImageWrapper(EImageFormat::JPEG);

    if (!ImageWrapper.IsValid())
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed to create ImageWrapper!"));
        return;
    }

    // Set image data and compress (high quality)
    ImageWrapper->SetRaw(
        ObjectThumbnail.GetUncompressedImageData().GetData(),
        ObjectThumbnail.GetUncompressedImageData().Num(),
        ObjectThumbnail.GetImageWidth(),
        ObjectThumbnail.GetImageHeight(),
        ERGBFormat::BGRA,
        8
    );
    
    const TArray64<uint8>& CompressedByteArray = ImageWrapper->GetCompressed(95);
    
    if (CompressedByteArray.Num() == 0)
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed to compress image data!"));
        return;
    }

    // Create directory if needed
    FString OutputDirectory = FPaths::GetPath(NewOutputPath);
    if (!IFileManager::Get().DirectoryExists(*OutputDirectory))
    {
        IFileManager::Get().MakeDirectory(*OutputDirectory, true);
    }

    // Save file
    if (FFileHelper::SaveArrayToFile(CompressedByteArray, *NewOutputPath))
    {
        UE_LOG(LogTemp, Log, TEXT("Exported thumbnail to: %s"), *NewOutputPath);
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed to save thumbnail to: %s"), *NewOutputPath);
    }
}