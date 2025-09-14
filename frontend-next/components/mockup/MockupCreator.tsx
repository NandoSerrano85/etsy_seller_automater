'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { FeatureGate, UsageIndicator } from '@/components/subscription';
import { useMockupStore } from '@/store/useMockupStore';
import { Step1Template } from './steps/Step1Template';
import { Step2Images } from './steps/Step2Images';
import { Step3Masks } from './steps/Step3Masks';
import { Step4Finalize } from './steps/Step4Finalize';

interface Template {
  id: string;
  name: string;
  thumbnail: string;
  category: string;
}

export function MockupCreator() {
  // Store integration
  const { masks } = useMockupStore();

  // Refs
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Workflow state
  const [currentTab, setCurrentTab] = useState('template');

  // Step 1: Template Selection
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  // Step 2: Image Selection
  const [selectedImages, setSelectedImages] = useState<string[]>([]);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [watermarkFile, setWatermarkFile] = useState<File | null>(null);

  // Step 3: Mask Creation
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [currentMaskIndex, setCurrentMaskIndex] = useState(0);
  const [allMasks, setAllMasks] = useState<Record<string, any>>({});
  const [maskModalOpen, setMaskModalOpen] = useState(false);

  // Step 4: Finalize
  const [mockupName, setMockupName] = useState('My Mockup');
  const [startingNumber, setStartingNumber] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);

  // Mock subscription data
  const canCreateMockups = true;
  const remainingMockups = 5;
  const isFreeTier = false;

  // Step 1 handlers
  const handleLoadTemplates = async () => {
    setLoadingTemplates(true);
    try {
      // Mock template loading
      await new Promise(resolve => setTimeout(resolve, 1000));
      const mockTemplates: Template[] = [
        {
          id: '1',
          name: 'T-Shirt Front',
          thumbnail: '/templates/tshirt-front.jpg',
          category: 'Apparel'
        },
        {
          id: '2',
          name: 'Mug Mockup',
          thumbnail: '/templates/mug.jpg',
          category: 'Drinkware'
        },
        {
          id: '3',
          name: 'Poster Frame',
          thumbnail: '/templates/poster.jpg',
          category: 'Print'
        },
        {
          id: '4',
          name: 'Phone Case',
          thumbnail: '/templates/phone-case.jpg',
          category: 'Tech'
        }
      ];
      setTemplates(mockTemplates);
    } catch (error) {
      console.error('Error loading templates:', error);
    } finally {
      setLoadingTemplates(false);
    }
  };

  const handleTemplateSelect = (template: Template) => {
    setSelectedTemplate(template);
  };

  // Step 2 handlers
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      const newFiles = Array.from(files);
      const newImages = newFiles.map(file => URL.createObjectURL(file));

      setImageFiles(prev => [...prev, ...newFiles]);
      setSelectedImages(prev => [...prev, ...newImages]);
    }
  };

  const handleWatermarkUpload = (file: File) => {
    setWatermarkFile(file);
  };

  const handleRemoveImage = (index: number) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index));
    setImageFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleRemoveWatermark = () => {
    setWatermarkFile(null);
  };

  // Step 3 handlers
  const handleImageSelect = (index: number) => {
    setCurrentImageIndex(index);
    setCurrentMaskIndex(0);
  };

  const handlePrevMask = () => {
    setCurrentMaskIndex(prev => Math.max(0, prev - 1));
  };

  const handleNextMask = () => {
    const currentImageMasks = allMasks[currentImageIndex] || {};
    const maskCount = Object.keys(currentImageMasks).length;
    setCurrentMaskIndex(prev => Math.min(maskCount - 1, prev + 1));
  };

  const handleCreateMask = () => {
    setMaskModalOpen(true);
  };

  const handleDeleteMask = () => {
    const currentImageMasks = { ...allMasks[currentImageIndex] || {} };
    delete currentImageMasks[currentMaskIndex];

    setAllMasks(prev => ({
      ...prev,
      [currentImageIndex]: currentImageMasks
    }));

    // Adjust current mask index if needed
    const remainingMasks = Object.keys(currentImageMasks).length;
    if (currentMaskIndex >= remainingMasks && remainingMasks > 0) {
      setCurrentMaskIndex(remainingMasks - 1);
    } else if (remainingMasks === 0) {
      setCurrentMaskIndex(0);
    }
  };

  // Step 4 handlers
  const handlePreview = () => {
    console.log('Preview mockup');
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      // Mock generation process
      await new Promise(resolve => setTimeout(resolve, 3000));
      console.log('Generated mockup:', {
        template: selectedTemplate,
        images: selectedImages.length,
        masks: Object.keys(allMasks).length,
        name: mockupName,
        startingNumber
      });
    } catch (error) {
      console.error('Error generating mockup:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  // Load templates on component mount
  useEffect(() => {
    handleLoadTemplates();
  }, []);

  return (
    <FeatureGate feature="mockup_creation">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Mockup Creator</h1>
              <p className="text-gray-600 mt-2">
                Create professional product mockups in 4 easy steps
              </p>
            </div>

            {isFreeTier && (
              <UsageIndicator
                current={10 - remainingMockups}
                max={10}
                label="Mockups Created"
                className="w-64"
              />
            )}
          </div>
        </div>

        {/* Workflow Tabs */}
        <Tabs value={currentTab} onValueChange={setCurrentTab} className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="template" className="flex items-center space-x-2">
              <span className="w-6 h-6 rounded-full bg-primary text-white text-xs flex items-center justify-center">1</span>
              <span>Template</span>
            </TabsTrigger>
            <TabsTrigger value="images" className="flex items-center space-x-2">
              <span className="w-6 h-6 rounded-full bg-primary text-white text-xs flex items-center justify-center">2</span>
              <span>Images</span>
            </TabsTrigger>
            <TabsTrigger value="masks" className="flex items-center space-x-2">
              <span className="w-6 h-6 rounded-full bg-primary text-white text-xs flex items-center justify-center">3</span>
              <span>Masks</span>
            </TabsTrigger>
            <TabsTrigger value="finalize" className="flex items-center space-x-2">
              <span className="w-6 h-6 rounded-full bg-primary text-white text-xs flex items-center justify-center">4</span>
              <span>Finalize</span>
            </TabsTrigger>
          </TabsList>

          <div className="flex-1">
            <TabsContent value="template" className="mt-0 h-full">
              <Step1Template
                templates={templates}
                selectedTemplate={selectedTemplate}
                setSelectedTemplate={setSelectedTemplate}
              />
            </TabsContent>

            <TabsContent value="images" className="mt-0 h-full">
              <Step2Images
                selectedImages={selectedImages}
                handleImageUpload={handleImageUpload}
              />
            </TabsContent>

            <TabsContent value="masks" className="mt-0 h-full">
              <Step3Masks
                canvasRef={canvasRef}
              />
            </TabsContent>

            <TabsContent value="finalize" className="mt-0 h-full">
              <Step4Finalize
                mockupName={mockupName}
                setMockupName={setMockupName}
                startingNumber={startingNumber}
                setStartingNumber={setStartingNumber}
              />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </FeatureGate>
  );
}